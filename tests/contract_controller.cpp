#define PASTILLERO_HOST_TEST 1
#include "../firmware/PastilleroESP32/PastilleroESP32.ino"
// Adaptador de pruebas: usa Controller del .ino y ArduinoJson real; no incluye Arduino ni GPIO.
#include <ArduinoJson.h>
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

struct ModelPort : pill::Port {
    std::vector<long> moves;
    JsonDocument reservations;
    JsonDocument output;
    bool rejectReservation = false;
    void move(long steps) override { moves.push_back(steps); }
    bool reached() override { return true; }
    bool handled(const char* id) override { return !reservations["done"][id].isNull(); }
    bool record(const pill::Dose& d, const char* kind, int64_t actual) override {
        if (rejectReservation) return false;
        pill::reserveDoseId(reservations, d);
        auto event = output["events"][std::string(d.id) + "-SIM-" + kind].to<JsonObject>();
        pill::writeDoseEvent(event, d, kind, actual, true);
        return true;
    }
};

int main() {
    try {
        std::string input, line;
        while (std::getline(std::cin, line)) {
            input += line;
            if (input.size() > 48000) throw std::runtime_error("Input exceeds QA limit");
        }
        JsonDocument message;
        if (deserializeJson(message, input)) throw std::runtime_error("Invalid JSON");
        auto program = message["program"];
        if (program["version"].as<int>() != 2 ||
            !pill::planModeMatches(program["targetMode"].as<const char*>(), true))
            throw std::runtime_error("Only simulation protocol V2 accepted by QA");
        ModelPort port;
        for (auto id : message["done"].as<JsonArray>())
            port.reservations["done"][id.as<std::string>()] = true;
        const std::string scenario = message["scenario"] | "confirmed";
        port.rejectReservation = scenario == "reservation_failure";
        pill::Controller controller(port);
        if (!controller.geometry(program["positions"] | 0))
            throw std::runtime_error("Invalid geometry");
        controller.calibrated = scenario != "uncalibrated";
        controller.requireExit = program["settings"]["exitSensorEnabled"] | false;
        for (JsonPair entry : program["doses"].as<JsonObject>()) {
            if (controller.count == 96) throw std::runtime_error("Too many doses");
            pill::Dose d;
            const std::string id = entry.key().c_str();
            const std::string medication = entry.value()["medicationId"] | "";
            if (id.size() > 36 || medication.size() > 36) throw std::runtime_error("Invalid ID");
            std::copy(id.c_str(), id.c_str() + id.size() + 1, d.id);
            std::copy(medication.c_str(), medication.c_str() + medication.size() + 1, d.medicationId);
            d.scheduledAt = entry.value()["scheduledAt"].as<int64_t>();
            d.compartment = entry.value()["compartment"].as<int>();
            if (!pill::validDose(d, controller.positions)) throw std::runtime_error("Invalid dose");
            controller.doses[controller.count++] = d;
        }
        int64_t first = INT64_MAX;
        for (int i = 0; i < controller.count; i++)
            first = std::min(first, controller.doses[i].scheduledAt);
        if (first == INT64_MAX) throw std::runtime_error("Expected QA doses");
        // El tiempo virtual queda en el pasado de la fixture: nunca se falsifica el reloj del host.
        int64_t epoch = scenario == "invalid_clock" ? 0
            : scenario == "not_due" ? message["now"].as<int64_t>()
            : first + (scenario == "missed" ? 300000 : 1000);
        uint32_t ms = 0;
        for (int iteration = 0; iteration < 40; iteration++) {
            controller.tick(ms++, epoch, scenario != "blocked", false);
            if (scenario == "interrupted" && !port.moves.empty()) break;
            if (controller.state == pill::State::Outward) {
                controller.tick(ms++, epoch, true, false, scenario != "no_exit");
                ms += 2000;
                epoch += 2000;
                controller.tick(ms++, epoch, true, false);
                controller.tick(ms++, epoch, true, false);
            }
            if (controller.state == pill::State::Awaiting && scenario == "confirmed")
                controller.tick(ms++, epoch, true, true);
            if (controller.state == pill::State::Alert) {
                controller.tick(ms++, epoch, true, false);
                controller.tick(ms++, epoch, true, true);
            }
            if (controller.state == pill::State::Fault) break;
        }
        for (auto steps : port.moves) port.output["moves"].add(steps);
        for (JsonPair reservation : port.reservations["done"].as<JsonObject>())
            port.output["done"].add(std::string(reservation.key().c_str()));
        port.output["state"] = static_cast<int>(controller.state);
        port.output["positions"] = controller.positions;
        port.output["hardwareUsed"] = false;
        port.output["simulation"] = true;
        serializeJson(port.output, std::cout);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what();
        return 2;
    }
}

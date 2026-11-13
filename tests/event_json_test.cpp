#define PASTILLERO_HOST_TEST 1
#include "../firmware/PastilleroESP32/PastilleroESP32.ino"
#include <ArduinoJson.h>
#include <assert.h>
#include <stdio.h>
#include <string>

// Regresión de los arreglos const: el JSON no puede apuntar a active, que cambia en la siguiente dosis.
int main() {
    JsonDocument doc;
    pill::Dose reused;
    strcpy(reused.id, "dose-a");
    strcpy(reused.medicationId, "med-a");
    reused.compartment = 4;
    reused.scheduledAt = 1800000000000LL;
    pill::writeDoseEvent(doc["first"].to<JsonObject>(), reused, "STARTED", 1800000001000LL, true);
    strcpy(reused.id, "dose-b");
    strcpy(reused.medicationId, "med-b");
    reused.compartment = 1;
    pill::writeDoseEvent(doc["second"].to<JsonObject>(), reused, "CONFIRMED", 1800000002000LL, true);
    assert(!strcmp(doc["first"]["doseId"], "dose-a"));
    assert(!strcmp(doc["first"]["medicationId"], "med-a"));
    assert(doc["first"]["compartment"].as<int>() == 4);
    assert(!strcmp(doc["second"]["doseId"], "dose-b"));
    int passed = 1;
    {
        pill::Dose temporary;
        strcpy(temporary.id, "short-id");
        strcpy(temporary.medicationId, "x");
        pill::writeDoseEvent(doc["temporary"].to<JsonObject>(), temporary, "MISSED", 1000, true);
        memset(temporary.id, 'z', sizeof(temporary.id));
        memset(temporary.medicationId, 'z', sizeof(temporary.medicationId));
    }
    assert(doc["temporary"]["doseId"].as<std::string>() == "short-id");
    assert(doc["temporary"]["medicationId"].as<std::string>() == "x");
    passed++;
    reused.medicationId[0] = '\0';
    pill::writeDoseEvent(doc["legacy"].to<JsonObject>(), reused, "RECOVERY", 1000, true);
    assert(doc["legacy"]["medicationId"].is<const char*>());
    assert(doc["legacy"]["medicationId"].as<std::string>().empty());
    passed++;
    doc["active"].set(doc["first"]);
    std::string serialized;
    serializeJson(doc, serialized);
    JsonDocument restored;
    assert(!deserializeJson(restored, serialized));
    assert(restored["active"]["doseId"].as<std::string>() == "dose-a");
    assert(restored["first"]["doseId"].as<std::string>() == "dose-a");
    assert(restored["second"]["medicationId"].as<std::string>() == "med-b");
    passed++;
    JsonDocument reservations;
    strcpy(reused.id, "reserved-a");
    pill::reserveDoseId(reservations, reused);
    strcpy(reused.id, "reserved-b");
    assert(reservations["done"]["reserved-a"].as<bool>());
    assert(reservations["done"]["reserved-b"].isNull());
    pill::reserveDoseId(reservations, reused);
    strcpy(reused.id, "reserved-c");
    assert(reservations["done"]["reserved-a"].as<bool>());
    assert(reservations["done"]["reserved-b"].as<bool>());
    assert(reservations["done"].size() == 2);
    passed++;
    serialized.clear();
    serializeJson(reservations, serialized);
    assert(!deserializeJson(restored, serialized));
    assert(restored["done"]["reserved-a"].as<bool>());
    assert(restored["done"]["reserved-b"].as<bool>());
    passed++;
    printf("PASS: %d shared event serializer ownership/short-ID/legacy/round-trip cases; no GPIO\n", passed);
}

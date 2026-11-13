#define PASTILLERO_HOST_TEST 1
#include "../firmware/PastilleroESP32/PastilleroESP32.ino"
#include <assert.h>
#include <stdio.h>
#include <string>
#include <vector>
using namespace pill;
constexpr int64_t NOW = 1800000000000LL;
struct FakeV2 : Port {
    std::vector<long> moves;
    std::vector<std::string> records, done;
    void move(long p) override {
        moves.push_back(p);
    }
    bool reached() override {
        return true;
    }
    bool handled(const char* id) override {
        for (auto& v : done)
            if (v == id)
                return true;
        return false;
    }
    bool record(const Dose& d, const char* type, int64_t) override {
        records.push_back(type);
        done.push_back(d.id);
        return true;
    }
};
void prepare(Controller& c, int comp = 2) {
    strcpy(c.doses[0].id, "v2-dose");
    c.doses[0].scheduledAt = NOW;
    c.doses[0].compartment = comp;
    c.count = 1;
    c.calibrated = true;
}
void delivered(Controller& c, bool exit) {
    c.tick(0, NOW, true, false);
    c.tick(1, NOW, true, false, exit);
    c.tick(2001, NOW, true, false);
    c.tick(2002, NOW, true, false);
}
int main() {
    int n = 0;
    {
        FakeV2 f;
        Controller c(f);
        prepare(c);
        delivered(c, false);
        assert(c.state == State::Awaiting);
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        assert(c.geometry(5));
        prepare(c, 4);
        delivered(c, false);
        assert(f.moves[0] == 2560 && f.moves[1] == 0);
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        prepare(c);
        assert(c.geometry(5));
        assert(!c.calibrated);
        assert(!c.geometry(6));
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        prepare(c);
        c.tick(0, NOW, true, false);
        assert(!c.geometry(5));
        n++;
    }
    {
        Dose d;
        strcpy(d.id, "valid");
        d.scheduledAt = NOW;
        d.compartment = 4;
        assert(!validDose(d));
        assert(validDose(d, 5));
        assert(!validDose(d, 6));
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        prepare(c);
        c.requireExit = true;
        delivered(c, false);
        assert(c.state == State::Alert);
        assert(f.records.back() == "NO_EXIT");
        c.tick(2003, NOW, true, true);
        assert(f.records.back() == "NO_EXIT");
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        prepare(c);
        c.requireExit = true;
        delivered(c, true);
        assert(c.state == State::Awaiting);
        c.tick(2003, NOW, true, true);
        assert(f.records.back() == "CONFIRMED");
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        prepare(c);
        c.requireExit = true;
        c.tick(0, NOW - 1, true, false, true);
        delivered(c, false);
        assert(c.state == State::Alert);
        n++;
    }
    {
        ExitDetector d;
        assert(!d.sample(false, 0));
        assert(!d.sample(true, 1));
        assert(!d.sample(false, 5));
        assert(!d.sample(true, 6));
        assert(!d.sample(true, 15));
        assert(d.sample(true, 16));
        assert(!d.sample(true, 50));
        n++;
    }
    {
        ExitDetector d;
        assert(!d.sample(true, 0));
        assert(!d.sample(true, 20));
        assert(!d.sample(false, 30));
        assert(!d.sample(false, 40));
        assert(!d.sample(true, 50));
        assert(d.sample(true, 60));
        n++;
    }
    {
        PeripheralSettings p;
        Feedback f;
        f.tick(State::Awaiting, 50, false, p);
        assert(f.ready && f.buzzer && !f.pump && !f.servoOpen);
        p.ledEnabled = p.buzzerEnabled = false;
        f.tick(State::Alert, 50, false, p);
        assert(!f.ready && !f.alert && !f.buzzer);
        n++;
    }
    {
        PeripheralSettings p;
        Feedback f;
        f.tick(State::Idle, 0, true, p);
        assert(!f.pump);
        p.pumpEnabled = true;
        f.tick(State::Idle, 1, false, p);
        f.tick(State::Idle, 2, true, p);
        assert(f.pump);
        f.tick(State::Idle, 2001, false, p);
        assert(f.pump);
        f.tick(State::Idle, 2002, false, p);
        assert(!f.pump);
        n++;
    }
    {
        PeripheralSettings p;
        p.pumpEnabled = true;
        Feedback f;
        f.tick(State::Alert, 10, false, p);
        assert(!f.pump);
        f.tick(State::Idle, 11, false, p);
        assert(!f.pump);
        f.tick(State::Idle, 12, true, p);
        assert(f.pump);
        f.tick(State::Fault, 13, false, p);
        assert(!f.pump);
        n++;
    }
    {
        PeripheralSettings p;
        p.pumpEnabled = true;
        Feedback f;
        f.tick(State::Idle, 1, true, p);
        f.tick(State::Idle, 2001, true, p);
        assert(!f.pump);
        f.tick(State::Idle, 2002, true, p);
        assert(!f.pump);
        n++;
    }
    {
        PeripheralSettings p;
        p.servoEnabled = true;
        Feedback f;
        f.tick(State::Drop, 0, false, p);
        assert(f.servoOpen);
        f.tick(State::Returning, 1, false, p);
        assert(!f.servoOpen);
        n++;
    }
    {
        char a[17], b[17];
        Feedback::lcd(State::Outward, 4, true, a, b);
        assert(strlen(a) <= 16 && strlen(b) <= 16);
        assert(strstr(a, "Dispensando"));
        Feedback::lcd(State::Alert, 1, false, a, b);
        assert(strstr(a, "ALERTA"));
        n++;
    }
    {
        PeripheralSettings p;
        p.pumpEnabled = true;
        Feedback f;
        f.tick(State::Idle, 0xfffffff0u, true, p);
        assert(f.pump);
        f.tick(State::Idle, 0x800u, false, p);
        assert(!f.pump);
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        prepare(c);
        c.count = 2;
        c.doses[1] = c.doses[0];
        strcpy(c.doses[1].id, "other-medication");
        c.doses[1].compartment = 1;
        delivered(c, false);
        c.tick(2003, NOW, true, true);
        c.tick(2004, NOW, true, false);
        assert(f.records.size() == 3 && f.records.back() == "STARTED");
        n++;
    }
    {
        FakeV2 f;
        Controller c(f);
        assert(c.geometry(5));
        c.calibrated = true;
        assert(c.manualStart(0));
        uint32_t ms = 0;
        for (int i = 1; i <= 4; i++) {
            c.tick(++ms, NOW, true, false);
            ms += 2000;
            c.tick(ms, NOW, true, false);
            c.tick(++ms, NOW, true, false);
            ms += 15000;
            c.tick(ms, NOW, true, false);
        }
        assert(c.state == State::Idle);
        assert((f.moves == std::vector<long>{640, 0, 1280, 0, 1920, 0, 2560, 0}));
        n++;
    }
    {
        char a[17], b[17];
        Feedback::lcd(State::Alert, 4, true, a, b, "NO_EXIT");
        assert(!strcmp(a, "Sin salida"));
        Feedback::lcd(State::Alert, 4, true, a, b, "MISSED");
        assert(!strcmp(a, "Dosis omitida"));
        n++;
    }
    printf("PASS: %d V2 geometry/sensor/LCD/servo/pump/LED/queue cases; no GPIO accessed\n", n);
}

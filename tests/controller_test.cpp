#define PASTILLERO_HOST_TEST 1
#include "../firmware/PastilleroESP32/PastilleroESP32.ino"
#include <assert.h>
#include <stdio.h>
#include <set>
#include <string>
#include <vector>
using namespace pill;
constexpr int64_t T = 1800000000000LL;
struct Fake : Port {
    std::vector<long> moves;
    std::vector<std::string> events;
    std::set<std::string> done;
    bool arrived = true, save = true;
    void move(long p) override {
        moves.push_back(p);
    }
    bool reached() override {
        return arrived;
    }
    bool handled(const char* id) override {
        return done.count(id);
    }
    bool record(const Dose& d, const char* type, int64_t) override {
        if (!save)
            return false;
        done.insert(d.id);
        events.push_back(type);
        return true;
    }
};
void due(Controller& c, int64_t at = T) {
    c.calibrated = true;
    c.count = 1;
    strcpy(c.doses[0].id, "dose-1");
    c.doses[0].scheduledAt = at;
    c.doses[0].compartment = 2;
}
void await(Controller& c, bool pressed = false) {
    c.tick(0, T, true, pressed);  // starts
    c.tick(1, T, true, pressed);  // reached outward
    c.tick(2000, T, true, pressed);
    assert(c.state == State::Drop);
    c.tick(2001, T, true, pressed);  // return
    c.tick(2002, T, true, pressed);
    assert(c.state == State::Awaiting);
}
int main() {
    int passed = 0;
    {
        Fake f;
        Controller c(f);
        assert(!c.manualStart(0));
        assert(f.moves.empty());
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        c.calibrated = true;
        assert(c.manualStart(0));
        for (uint32_t start : {0u, 17002u, 34004u}) {
            c.tick(start + 1, T, true, false);
            c.tick(start + 2000, T, true, false);
            assert(c.state == State::Drop);
            c.tick(start + 2001, T, true, false);
            c.tick(start + 2002, T, true, false);
            c.tick(start + 17001, T, true, false);
            assert(c.state == State::ManualGap);
            c.tick(start + 17002, T, true, false);
        }
        assert((f.moves == std::vector<long>{800, 0, 1600, 0, 2400, 0}));
        assert(c.state == State::Idle);
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        c.tick(0, T, true, false);
        f.arrived = false;
        for (int i = 1; i < 10000; i++)
            c.tick(i, T, true, true);
        assert(c.state == State::Outward);
        assert(f.moves.size() == 1);
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        await(c, true);
        c.tick(2003, T, true, true);
        assert(c.state == State::Awaiting);
        c.tick(2004, T, true, false);
        c.tick(2005, T + 10000, true, true);
        assert(c.state == State::Idle);
        assert(f.events.back() == "CONFIRMED");
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        await(c);
        c.tick(300000, T + OMIT_MS, true, true);
        assert(c.state == State::Alert);
        assert(f.events.back() == "MISSED");
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        c.tick(0, 0, true, false);
        assert(f.moves.empty());
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        c.tick(0, T, false, false);
        assert(c.state == State::Alert);
        assert(f.events.back() == "BLOCKED");
        assert(f.moves.empty());
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        f.save = false;
        c.tick(0, T, true, false);
        assert(c.state == State::Fault);
        assert(f.moves.empty());
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        f.done.insert("dose-1");
        c.tick(0, T, true, false);
        assert(f.moves.empty());
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        c.calibrated = false;
        c.tick(0, T + OMIT_MS, true, false);
        assert(f.events.back() == "MISSED");
        assert(f.moves.empty());
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        await(c);
        c.tick(299999, T + OMIT_MS - 1, true, true);
        assert(c.state == State::Idle);
        assert(f.events.back() == "CONFIRMED");
        passed++;
    }
    {
        Dose d;
        strcpy(d.id, "valid-1");
        d.scheduledAt = T;
        d.compartment = 3;
        assert(validDose(d));
        d.compartment = 4;
        assert(!validDose(d));
        d.compartment = 1;
        strcpy(d.id, "bad/id");
        assert(!validDose(d));
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        c.calibrated = true;
        assert(c.manualStart(0xFFFFFFF0u));
        c.tick(0xFFFFFFF1u, T, true, false);
        c.tick(1985, T, true, false);
        assert(c.state == State::Returning);
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        await(c);
        f.save = false;
        c.tick(2003, T, true, true);
        assert(c.state == State::Fault);
        passed++;
    }
    {
        Fake f;
        Controller c(f);
        due(c);
        f.arrived = false;
        c.tick(0, T, true, false);
        assert(f.moves.empty());
        passed++;
    }
    assert(
        !strcmp(commandDecision("PING", "simulation", true, T, T + 600000, T + 1000, 0, 0), "OK"));
    passed++;
    assert(!strcmp(commandDecision("DISPENSE", "simulation", true, T, T + 600000, T + 1000, 0, 0),
                   "UNKNOWN_COMMAND"));
    passed++;
    assert(!strcmp(commandDecision("PING", "hardware", true, T, T + 600000, T + 1000, 0, 0),
                   "WRONG_MODE"));
    passed++;
    assert(!strcmp(commandDecision("PING", "simulation", true, T, T + 600000, T + 600000, 0, 0),
                   "EXPIRED_OR_INVALID_TIME"));
    passed++;
    assert(!strcmp(commandDecision("APPLY_PLAN", "simulation", true, T, T + 600000, T + 1000, 3, 2),
                   "WAIT"));
    passed++;
    for (int retry = 0; retry < 3; retry++)
        assert(!strcmp(
            commandDecision("APPLY_PLAN", "simulation", true, T, T + 600000, T + 1000, 3, 3),
            "OK"));
    passed++;
    assert(!strcmp(commandDecision("PING", "simulation", true, T, T + 600000, T + 1000, 1, 0),
                   "INVALID_REVISION"));
    passed++;
    assert(planModeMatches("simulation", true) && !planModeMatches("simulation", false));
    passed++;
    assert(planModeMatches("hardware", false) && !planModeMatches(nullptr, false));
    passed++;
    printf("PASS: %d firmware controller/command cases; no serial ports or GPIO accessed\n",
           passed);
}

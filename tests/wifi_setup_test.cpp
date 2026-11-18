#define PASTILLERO_HOST_TEST 1
#include "../firmware/PastilleroESP32/PastilleroESP32.ino"
#include <assert.h>
#include <stdio.h>
#include <initializer_list>
using namespace pill;
struct ConfirmPort : Port {
    bool reserved = false; int confirmations = 0;
    void move(long) override {}
    bool reached() override { return true; }
    bool handled(const char*) override { return reserved; }
    bool record(const Dose&, const char* type, int64_t) override {
        if (!strcmp(type, "STARTED")) reserved = true;
        if (!strcmp(type, "CONFIRMED")) confirmations++;
        return true;
    }
};
int main() {
    int count = 0;
    { // No se configura red mientras hay giro, espera de toma o alerta.
        assert(wifiSetupAllowed(State::Idle, true));
        assert(!wifiSetupAllowed(State::Idle, false));
        for (State state : {State::Outward, State::Drop, State::Returning, State::Awaiting, State::Alert, State::Fault})
            assert(!wifiSetupAllowed(state, true));
        count++;
    }
    { // La pulsación larga exige soltar antes y solo dispara una vez.
        bool armed = false, timing = false; uint32_t since = 0;
        assert(!wifiButtonRequest(true, true, 0, armed, timing, since));
        assert(!wifiButtonRequest(true, false, 1, armed, timing, since));
        assert(!wifiButtonRequest(true, true, 2, armed, timing, since));
        assert(!wifiButtonRequest(true, true, 8001, armed, timing, since));
        assert(wifiButtonRequest(true, true, 8002, armed, timing, since));
        assert(!wifiButtonRequest(true, true, 16002, armed, timing, since)); count++;
    }
    { // Mantener el botón usado para confirmar no abre configuración al volver a Idle.
        bool armed = true, timing = true; uint32_t since = 0;
        assert(!wifiButtonRequest(false, true, 100, armed, timing, since));
        assert(!wifiButtonRequest(true, true, 20000, armed, timing, since));
        assert(!wifiButtonRequest(true, false, 20001, armed, timing, since));
        assert(!wifiButtonRequest(true, true, 20002, armed, timing, since));
        assert(wifiButtonRequest(true, true, 28002, armed, timing, since)); count++;
    }
    { // millis puede desbordarse sin convertir la ventana en infinita.
        uint32_t start = 0xfffffff0U;
        assert(!wifiSetupExpired(start + 299999U, start));
        assert(wifiSetupExpired(start + 300000U, start)); count++;
    }
    { // Una pulsación en espera confirma: avisos apagados al entrar en reposo.
        Feedback f; PeripheralSettings p;
        f.tick(State::Awaiting, 1000, false, p); assert(f.ready && f.buzzer);
        f.tick(State::Idle, 1001, true, p);
        assert(!f.ready && !f.alert && !f.buzzer && f.confirmationVisible); count++;
    }
    { // El mensaje termina a los cinco segundos y no se renueva por mantener la señal.
        Feedback f; PeripheralSettings p;
        f.tick(State::Idle, 10, true, p);
        f.tick(State::Idle, 5009, true, p); assert(f.confirmationVisible);
        f.tick(State::Idle, 5010, true, p); assert(!f.confirmationVisible); count++;
    }
    { // Una nueva dispensación tiene prioridad sobre el texto de la confirmación anterior.
        Feedback f; PeripheralSettings p;
        f.tick(State::Idle, 0, true, p);
        f.tick(State::Outward, 1, false, p); assert(!f.confirmationVisible); count++;
    }
    { // El aviso cabe en LCD 16x2, sin cortar el mensaje de toma.
        char first[17]{}, second[17]{};
        Feedback::lcd(State::Awaiting, 1, false, first, second);
        assert(!strcmp(first, "Toma tu pastilla")); count++;
    }
    { // La señal de botón pasa por Controller: una toma y apagado de avisos, sin duplicación.
        ConfirmPort io; Controller c(io); c.geometry(5); c.calibrated = true;
        strcpy(c.doses[0].id, "dose-button"); c.doses[0].scheduledAt = 1800000000000LL;
        c.doses[0].compartment = 1; c.count = 1;
        c.tick(0, 1800000000000LL, true, false);
        c.tick(1, 1800000000001LL, true, false);
        c.tick(2001, 1800000002001LL, true, false);
        c.tick(2002, 1800000002002LL, true, false);
        assert(c.state == State::Awaiting);
        Feedback f; PeripheralSettings p; f.tick(c.state, 3000, false, p); assert(f.buzzer && f.ready);
        c.tick(3001, 1800000003001LL, true, true);
        assert(c.state == State::Idle && io.confirmations == 1);
        f.tick(c.state, 3001, true, p); assert(!f.buzzer && !f.ready && !f.alert);
        c.tick(3002, 1800000003002LL, true, true); assert(io.confirmations == 1); count++;
    }
    printf("PASS: %d Wi-Fi/button/confirmation policy cases; PC only, no radio/GPIO/NVS hardware\n", count);
}

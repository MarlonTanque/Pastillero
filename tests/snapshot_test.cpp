#define PASTILLERO_HOST_TEST 1
#include "../firmware/PastilleroESP32/PastilleroESP32.ino"
#include <ArduinoJson.h>
#include <assert.h>
#include <map>
#include <stdio.h>
#include <string>
#include <vector>

// Doble en RAM de Preferences: prueba el contrato compartido, no simula la flash física.
struct MemoryStore {
    std::map<std::string, std::string> values;
    std::map<std::string, unsigned char> markers;
    bool shortWrite = false, markerFailure = false, shortRead = false;
    int writes = 0;
    bool isKey(const char* key) { return values.count(key) || markers.count(key); }
    unsigned char getUChar(const char* key, unsigned char fallback) {
        return markers.count(key) ? markers[key] : fallback;
    }
    size_t putUChar(const char* key, unsigned char value) {
        if (markerFailure) return 0;
        markers[key] = value;
        return 1;
    }
    size_t putBytes(const char* key, const void* data, size_t length) {
        writes++;
        size_t written = shortWrite ? length - 1 : length;
        values[key] = std::string(static_cast<const char*>(data), written);
        return written;
    }
    size_t getBytesLength(const char* key) { return values[key].size(); }
    size_t getBytes(const char* key, void* data, size_t length) {
        size_t read = values[key].size() < length ? values[key].size() : length;
        if (shortRead && read) read--;
        memcpy(data, values[key].data(), read);
        return read;
    }
};

int main() {
    int passed = 0;
    {
        JsonDocument doc;
        doc["protocolVersion"] = 2;
        for (int i = 0; i < 96; ++i) {
            std::string id = "dose-" + std::to_string(i);
            doc["plan"]["doses"][id]["scheduledAt"] = 1800000000000LL + i * 60000;
            doc["plan"]["doses"][id]["compartment"] = i % 4 + 1;
            doc["plan"]["doses"][id]["medicationId"] = "medication-one";
        }
        doc["done"]["delivered"] = true;
        doc["events"]["delivered-SIM-CONFIRMED"]["doseId"] = "delivered";
        std::string json;
        serializeJson(doc, json);
        assert(json.size() > 4000 && json.size() <= pill::SNAPSHOT_MAX_BYTES);
        MemoryStore store;
        assert(pill::saveSnapshotBlob(store, json.data(), json.size()));
        assert(pill::snapshotSource(store) == pill::SnapshotSource::Blob);
        size_t size = pill::snapshotBlobSize(store);
        std::vector<char> bytes(size + 1);
        assert(pill::readSnapshotBlob(store, bytes.data(), bytes.size(), size));
        JsonDocument restored;
        assert(!deserializeJson(restored, bytes.data()));
        assert(restored["plan"]["doses"].size() == 96);
        assert(restored["done"]["delivered"].as<bool>());
        assert(restored["events"]["delivered-SIM-CONFIRMED"]["doseId"] == "delivered");
        assert(store.markers["snapshot-ver"] == 2);
        passed++;
    }
    {
        MemoryStore store;
        std::string tooLarge(pill::SNAPSHOT_MAX_BYTES + 1, 'x');
        assert(!pill::saveSnapshotBlob(store, "", 0));
        assert(!pill::saveSnapshotBlob(store, nullptr, 10));
        assert(!pill::saveSnapshotBlob(store, tooLarge.data(), tooLarge.size()));
        assert(store.writes == 0);
        passed++;
    }
    {
        MemoryStore store;
        store.shortWrite = true;
        assert(!pill::saveSnapshotBlob(store, "{}", 2));
        assert(!store.markers.count("snapshot-ver"));
        passed++;
    }
    {
        MemoryStore store;
        store.values["snapshot"] = "old-reservations";
        store.markerFailure = true;
        const char* reserved = "{\"done\":{\"new\":true}}";
        assert(!pill::saveSnapshotBlob(store, reserved, strlen(reserved)));
        // Aunque falle el marcador, el bloque escrito conserva prioridad al reiniciar.
        assert(pill::snapshotSource(store) == pill::SnapshotSource::Blob);
        passed++;
    }
    {
        MemoryStore store;
        assert(pill::snapshotSource(store) == pill::SnapshotSource::Fresh);
        store.values["snapshot"] = "{}";
        assert(pill::snapshotSource(store) == pill::SnapshotSource::LegacyString);
        store.markers["snapshot-ver"] = 2;
        assert(pill::snapshotSource(store) == pill::SnapshotSource::Invalid);
        store.markers["snapshot-ver"] = 99;
        assert(pill::snapshotSource(store) == pill::SnapshotSource::Invalid);
        passed++;
    }
    {
        MemoryStore store;
        store.values["snapshot"] = "old-copy";
        store.values["snapshot-v2"] = "";
        assert(pill::snapshotSource(store) == pill::SnapshotSource::Blob);
        assert(pill::snapshotBlobSize(store) == 0);
        store.values["snapshot-v2"] = std::string(pill::SNAPSHOT_MAX_BYTES + 1, 'x');
        assert(pill::snapshotBlobSize(store) == 0);
        store.values["snapshot-v2"] = "{}";
        store.shortRead = true;
        char bytes[3]{};
        assert(!pill::readSnapshotBlob(store, bytes, sizeof(bytes), 2));
        passed++;
    }
    {
        MemoryStore store;
        store.values["snapshot-v2"] = std::string("a\0b", 3);
        char bytes[4]{};
        assert(!pill::readSnapshotBlob(store, bytes, sizeof(bytes), 3));
        passed++;
    }
    {
        MemoryStore store;
        store.values["snapshot-v2"] = "{}";
        char bytes[3] = {'x', 'x', '!'};
        assert(!pill::readSnapshotBlob(store, bytes, 2, 2));
        assert(bytes[0] == 'x' && bytes[2] == '!');
        assert(!pill::readSnapshotBlob(store, nullptr, 3, 2));
        assert(pill::readSnapshotBlob(store, bytes, 3, 2));
        assert(bytes[2] == '\0');
        passed++;
    }
    printf("PASS: %d shared snapshot blob/legacy/failure/bounds cases; RAM fake, no NVS hardware\n", passed);
}

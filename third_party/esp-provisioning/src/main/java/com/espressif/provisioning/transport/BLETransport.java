// Copyright 2020 Espressif Systems (Shanghai) PTE LTD
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


package com.espressif.provisioning.transport;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothProfile;
import android.content.Context;
import android.os.Build;
import com.espressif.provisioning.PrivateLog;

import com.espressif.provisioning.DeviceConnectionEvent;
import com.espressif.provisioning.ESPConstants;
import com.espressif.provisioning.listeners.ResponseListener;

import org.greenrobot.eventbus.EventBus;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;

/**
 * Bluetooth implementation of the Transport protocol.
 */
public class BLETransport implements Transport {

    private static final String TAG = "Espressif::" + BLETransport.class.getSimpleName();

    private Context context;
    private BluetoothDevice currentDevice;
    private BluetoothGatt bluetoothGatt;
    private BluetoothGattService service;
    private ResponseListener currentResponseListener;
    private Semaphore transportToken;
    private ExecutorService dispatcherThreadPool;
    private HashMap<String, String> uuidMap = new HashMap<>();
    private ArrayList<String> charUuidList = new ArrayList<>();

    private String serviceUuid;
    private boolean isReadingDescriptors = false;
    public ArrayList<String> deviceCapabilities = new ArrayList<>();
    public String versionInfo;

    /**
     * Create BLETransport implementation
     *
     * @param context
     */
    public BLETransport(Context context) {
        this.context = context;
        this.transportToken = new Semaphore(1);
        this.dispatcherThreadPool = Executors.newSingleThreadExecutor();
    }

    /**
     * BLE implementation of Transport protocol
     *
     * @param path     path of the config endpoint.
     * @param data     config data to be sent
     * @param listener listener implementation which receives events when response is received.
     */
    @Override
    public void sendConfigData(String path, byte[] data, ResponseListener listener) {

        if (uuidMap.containsKey(path)) {

            BluetoothGattCharacteristic characteristic = service.getCharacteristic(UUID.fromString(uuidMap.get(path)));

            if (characteristic == null) {
                characteristic = service.getCharacteristic(UUID.fromString("0000ff52-0000-1000-8000-00805f9b34fb"));
            }

            if (characteristic != null) {
                try {
                    this.transportToken.acquire();
                    characteristic.setValue(data);
                    bluetoothGatt.writeCharacteristic(characteristic);
                    currentResponseListener = listener;
                } catch (Exception e) {
                    /* Sin registrar mensajes que puedan contener datos locales. */
                    listener.onFailure(e);
                    this.transportToken.release();
                    currentResponseListener = listener;
                    if (currentResponseListener != null) {
                        currentResponseListener.onFailure(e);
                    }
                }
            } else {
                PrivateLog.e(TAG, "Characteristic is not available for given path.");
                currentResponseListener = listener;
                if (currentResponseListener != null) {
                    currentResponseListener.onFailure(new RuntimeException("Characteristic is not available for given path."));
                }
            }
        } else {
            currentResponseListener = listener;
            PrivateLog.e(TAG, "Characteristic is not available for given path.");
            if (currentResponseListener != null) {
                currentResponseListener.onFailure(new RuntimeException("Characteristic is not available for given path."));
            }
        }
    }

    /**
     * Connect to a BLE peripheral device.
     *
     * @param bluetoothDevice    The peripheral device
     * @param primaryServiceUuid Primary Service UUID
     */
    public void connect(BluetoothDevice bluetoothDevice, UUID primaryServiceUuid) {
        this.currentDevice = bluetoothDevice;
        this.serviceUuid = primaryServiceUuid.toString();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            bluetoothGatt = this.currentDevice.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE);
        } else {
            bluetoothGatt = this.currentDevice.connectGatt(context, false, gattCallback);
        }
    }

    /**
     * Disconnect from the current connected peripheral
     */
    public void disconnect() {

        PrivateLog.e(TAG, "Disconnect device");

        if (this.bluetoothGatt != null) {
            this.bluetoothGatt.disconnect();
            this.bluetoothGatt.close();
            bluetoothGatt = null;
        }
    }

    public void refreshServices() {
        PrivateLog.e(TAG, "Refresh services...");
        try {
            // BluetoothGatt gatt
            final Method refresh = bluetoothGatt.getClass().getMethod("refresh");
            if (refresh != null) {
                refresh.invoke(bluetoothGatt);
            }
        } catch (Exception e) {
            /* Sin registrar mensajes que puedan contener datos locales. */
        }
        bluetoothGatt.discoverServices();
    }

    private BluetoothGattCallback gattCallback = new BluetoothGattCallback() {

        @Override
        public void onConnectionStateChange(BluetoothGatt gatt, int status, int newState) {

            super.onConnectionStateChange(gatt, status, newState);
            PrivateLog.d(TAG, "onConnectionStateChange, New state : " + newState + ", Status : " + status);

            if (status == BluetoothGatt.GATT_FAILURE) {
                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
                return;
            } else if (status == 133) {
                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
                return;
            } else if (status != BluetoothGatt.GATT_SUCCESS && newState != BluetoothProfile.STATE_DISCONNECTED) {
                // TODO need to check this status
                return;
            }

            if (newState == BluetoothProfile.STATE_CONNECTED) {
                PrivateLog.e(TAG, "Connected to GATT server.");
                gatt.requestMtu(512);
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                PrivateLog.e(TAG, "Disconnected from GATT server.");
                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_DISCONNECTED));
            }
        }

        @Override
        public void onServicesDiscovered(BluetoothGatt gatt, int status) {

            super.onServicesDiscovered(gatt, status);
            PrivateLog.d(TAG, "On services discovered");

            if (status != BluetoothGatt.GATT_SUCCESS) {
                PrivateLog.d(TAG, "Status not success");
                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
                return;
            }

            service = gatt.getService(UUID.fromString(serviceUuid));

            if (service == null) {
                PrivateLog.e(TAG, "Service not found!");
                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
                return;
            }

            for (BluetoothGattCharacteristic characteristic : service.getCharacteristics()) {

                if (characteristic == null) {
                    PrivateLog.e(TAG, "Tx characteristic not found!");
                    EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
                    return;
                }

                String uuid = characteristic.getUuid().toString();
                PrivateLog.d(TAG, "Characteristic UUID : " + uuid);
                charUuidList.add(uuid);

                characteristic.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT);
            }

            readNextDescriptor();
        }

        @Override
        public void onDescriptorWrite(BluetoothGatt gatt, BluetoothGattDescriptor descriptor, int status) {

            if (status == BluetoothGatt.GATT_SUCCESS) {
                PrivateLog.d(TAG, "Read Descriptor : " + bluetoothGatt.readDescriptor(descriptor));
            } else {
                PrivateLog.e(TAG, "Fail to write descriptor");
                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
            }
        }

        @Override
        public void onDescriptorRead(BluetoothGatt gatt, BluetoothGattDescriptor descriptor, int status) {

            PrivateLog.d(TAG, "DescriptorRead, : Status " + status);
            byte[] data = descriptor.getValue();
            String charUuid = descriptor.getCharacteristic().getUuid().toString();

            if (status != BluetoothGatt.GATT_SUCCESS) {
                PrivateLog.e(TAG, "Failed to read descriptor");
                charUuidList.remove(charUuid);
//                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
//                return;
            }

            if (data == null) {
                PrivateLog.e(TAG, "Descriptor value is null");
                charUuidList.remove(charUuid);
            } else {
                String value = new String(data, StandardCharsets.UTF_8);
                uuidMap.put(value, charUuid);
                PrivateLog.d(TAG, "DescriptorRead, Value : " + value + " for UUID : " + charUuid);
            }

            if (isReadingDescriptors) {

                readNextDescriptor();

            } else {

                BluetoothGattCharacteristic characteristic = service.getCharacteristic(UUID.fromString(uuidMap.get(ESPConstants.HANDLER_PROTO_VER)));

                if (characteristic != null) {
                    // Write anything. It doesn't matter. We need to read characteristic and for that we need to write something.
                    characteristic.setValue("ESP");
                    bluetoothGatt.writeCharacteristic(characteristic);
                }
            }
        }

        @Override
        public void onMtuChanged(BluetoothGatt gatt, int mtu, int status) {
            super.onMtuChanged(gatt, mtu, status);
            if (status == BluetoothGatt.GATT_SUCCESS) {
                PrivateLog.d(TAG, "Supported MTU = " + mtu);
            }
            gatt.discoverServices();
        }

        @Override
        public void onCharacteristicChanged(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
            PrivateLog.d(TAG, "onCharacteristicChanged");
            super.onCharacteristicChanged(gatt, characteristic);
        }

        @Override
        public void onCharacteristicRead(BluetoothGatt gatt,
                                         final BluetoothGattCharacteristic characteristic,
                                         int status) {

            PrivateLog.d(TAG, "onCharacteristicRead, status " + status + " UUID : " + characteristic.getUuid().toString());
            super.onCharacteristicRead(gatt, characteristic, status);

            if (uuidMap.get((ESPConstants.HANDLER_PROTO_VER)).equals(characteristic.getUuid().toString())) {

                String data = new String(characteristic.getValue(), StandardCharsets.UTF_8);
                PrivateLog.d(TAG, "Value : " + data);
                versionInfo = data;

                try {
                    JSONObject jsonObject = new JSONObject(data);
                    JSONObject provInfo = jsonObject.getJSONObject("prov");

                    String deviceVersion = provInfo.getString("ver");
                    PrivateLog.d(TAG, "Device Version : " + deviceVersion);

                    JSONArray capabilities = provInfo.getJSONArray("cap");

                    for (int i = 0; i < capabilities.length(); i++) {
                        String cap = capabilities.getString(i);
                        deviceCapabilities.add(cap);
                    }
                    PrivateLog.d(TAG, "Capabilities : " + deviceCapabilities);

                } catch (JSONException e) {
                    /* Sin registrar mensajes que puedan contener datos locales. */
                    PrivateLog.d(TAG, "Capabilities JSON not available.");
                }

                EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTED));
            }

            if (currentResponseListener != null) {

                if (status == BluetoothGatt.GATT_SUCCESS) {
                    /*
                     * Need to dispatch this on another thread since the caller
                     * might decide to enqueue another send operation on success
                     * of the first.
                     */
                    final ResponseListener responseListener = currentResponseListener;
                    dispatcherThreadPool.submit(new Runnable() {
                        @Override
                        public void run() {
                            currentResponseListener = null;
                            byte[] charValue = characteristic.getValue();
                            responseListener.onSuccess(charValue);
                        }
                    });
                } else {

                    currentResponseListener.onFailure(new Exception("Read from BLE failed"));
//                    EventBus.getDefault().post(new DeviceProvEvent(LibConstants.EVENT_DEVICE_COMMUNICATION_FAILED));
                }
            }
            transportToken.release();
        }

        @Override
        public void onCharacteristicWrite(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status) {

            PrivateLog.d(TAG, "onCharacteristicWrite, status : " + status);
            PrivateLog.d(TAG, "UUID : " + characteristic.getUuid().toString());
            super.onCharacteristicWrite(gatt, characteristic, status);

            if (status == BluetoothGatt.GATT_SUCCESS) {
                bluetoothGatt.readCharacteristic(characteristic);
            } else {
                if (currentResponseListener != null) {
                    currentResponseListener.onFailure(new Exception("Write to BLE failed"));
//                    EventBus.getDefault().post(new DeviceProvEvent(LibConstants.EVENT_DEVICE_COMMUNICATION_FAILED));
                }
                transportToken.release();
            }
        }
    };

    private void readNextDescriptor() {

        boolean found = false;

        for (int i = 0; i < charUuidList.size(); i++) {

            String uuid = charUuidList.get(i);

            if (!uuidMap.containsValue(uuid)) {

                // Read descriptor
                BluetoothGattCharacteristic characteristic = service.getCharacteristic(UUID.fromString(uuid));
                if (characteristic == null) {
                    PrivateLog.e(TAG, "Tx characteristic not found!");
                    disconnect();
                    EventBus.getDefault().post(new DeviceConnectionEvent(ESPConstants.EVENT_DEVICE_CONNECTION_FAILED));
                    return;
                }

                for (BluetoothGattDescriptor descriptor : characteristic.getDescriptors()) {
                    String desUuid = descriptor.getUuid().toString();
                    if (desUuid.contains(ESPConstants.USER_DESCRIPTION_UUID)) {
                        PrivateLog.d(TAG, "Descriptor read : " + bluetoothGatt.readDescriptor(descriptor));
                    }
                }
                found = true;
                break;
            }
        }

        if (found) {
            isReadingDescriptors = true;
        } else {

            isReadingDescriptors = false;

            BluetoothGattCharacteristic characteristic = service.getCharacteristic(UUID.fromString(uuidMap.get(ESPConstants.HANDLER_PROTO_VER)));

            if (characteristic != null) {
                characteristic.setValue("ESP");
                bluetoothGatt.writeCharacteristic(characteristic);
            }
        }
    }
}

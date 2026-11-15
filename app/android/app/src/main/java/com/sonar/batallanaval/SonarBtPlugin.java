package com.sonar.batallanaval;

import android.Manifest;
import android.annotation.SuppressLint;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;

import androidx.activity.result.ActivityResult;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;

/**
 * Complementa a @e-is/capacitor-bluetooth-serial, que NO pide permisos en Android 13+ ni lista
 * los dispositivos emparejados. Expone: ensurePermissions, enableBluetooth, bonded, bindWifi.
 */
@CapacitorPlugin(
    name = "SonarBt",
    permissions = {
        @Permission(strings = {Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_SCAN}, alias = "bt31"),
        @Permission(strings = {Manifest.permission.ACCESS_FINE_LOCATION}, alias = "bt30")
    }
)
public class SonarBtPlugin extends Plugin {

    private String alias() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ? "bt31" : "bt30";
    }

    private BluetoothAdapter adapter() {
        BluetoothManager m = (BluetoothManager) getContext().getSystemService(Context.BLUETOOTH_SERVICE);
        return m == null ? null : m.getAdapter();
    }

    private boolean granted() {
        return getPermissionState(alias()) == PermissionState.GRANTED;
    }

    /** Pide BLUETOOTH_CONNECT + BLUETOOTH_SCAN (API 31+) o ubicación (API ≤ 30). → {granted} */
    @PluginMethod
    public void ensurePermissions(PluginCall call) {
        if (granted()) { resolveGranted(call, true); return; }
        requestPermissionForAlias(alias(), call, "permsCallback");
    }

    @PermissionCallback
    private void permsCallback(PluginCall call) {
        resolveGranted(call, granted());
    }

    private void resolveGranted(PluginCall call, boolean g) {
        JSObject o = new JSObject();
        o.put("granted", g);
        call.resolve(o);
    }

    /** Muestra el diálogo del sistema «activar Bluetooth» si está apagado. → {enabled} */
    @PluginMethod
    @SuppressLint("MissingPermission")
    public void enableBluetooth(PluginCall call) {
        BluetoothAdapter a = adapter();
        if (a == null) { call.reject("Este dispositivo no tiene Bluetooth"); return; }
        if (a.isEnabled()) { resolveEnabled(call, true); return; }
        if (!granted()) { call.reject("Permiso de Bluetooth denegado"); return; }
        startActivityForResult(call, new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), "enableCallback");
    }

    @ActivityCallback
    private void enableCallback(PluginCall call, ActivityResult result) {
        if (call == null) return;
        BluetoothAdapter a = adapter();
        resolveEnabled(call, a != null && a.isEnabled());
    }

    private void resolveEnabled(PluginCall call, boolean e) {
        JSObject o = new JSObject();
        o.put("enabled", e);
        call.resolve(o);
    }

    /** Dispositivos ya emparejados. → {devices:[{name,address}]} */
    @PluginMethod
    @SuppressLint("MissingPermission")
    public void bonded(PluginCall call) {
        BluetoothAdapter a = adapter();
        if (a == null) { call.reject("Este dispositivo no tiene Bluetooth"); return; }
        if (!granted()) { call.reject("Permiso de Bluetooth denegado"); return; }
        JSArray arr = new JSArray();
        try {
            for (BluetoothDevice d : a.getBondedDevices()) {
                JSObject o = new JSObject();
                o.put("name", d.getName() == null ? "" : d.getName());
                o.put("address", d.getAddress());
                arr.put(o);
            }
        } catch (SecurityException e) {
            call.reject("Permiso de Bluetooth denegado");
            return;
        }
        JSObject res = new JSObject();
        res.put("devices", arr);
        call.resolve(res);
    }

    /**
     * Android manda el tráfico por datos móviles si el Wi-Fi «no tiene internet» (caso del AP del ESP32).
     * Esto ata el proceso a la red Wi-Fi para que 192.168.4.1 sea alcanzable. → {bound}
     */
    @PluginMethod
    @SuppressWarnings("deprecation")
    public void bindWifi(PluginCall call) {
        ConnectivityManager cm = (ConnectivityManager) getContext().getSystemService(Context.CONNECTIVITY_SERVICE);
        boolean bound = false;
        if (cm != null) {
            for (Network n : cm.getAllNetworks()) {
                NetworkCapabilities c = cm.getNetworkCapabilities(n);
                if (c != null && c.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
                    bound = cm.bindProcessToNetwork(n);
                    break;
                }
            }
        }
        JSObject o = new JSObject();
        o.put("bound", bound);
        call.resolve(o);
    }
}

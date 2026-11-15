package com.sonar.batallanaval;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(SonarBtPlugin.class); // permisos, emparejados y Wi-Fi (complemento del plugin serial)
        super.onCreate(savedInstanceState);
    }
}

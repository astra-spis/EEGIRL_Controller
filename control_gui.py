import PySimpleGUI as sg
import numpy as np
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder

# EEGIRL_Controller/connect_port.py
import connect_port
# EEGIOL_Controller/process_ssvep.py
import process_ssvep

# Setting application format
bg_color = '#282923'

def main():
    toggle_connect = False
    serial_port = ""
    switch_code = 2
    down_con = True
    down_exe = True
    down_osc = True
    down_mid = False
    down_pow = True

    # Window Theme
    sg.theme('Dark Brown')

    # Menu Bar
    menu_def = [['File', ['Exit']], ['View', ['Top', 'Clear']]]

    # Get Port List
    ports = connect_port.search_port()

    # Left Top Frame
    widet_device = [
        sg.Text('COM Port'),
        sg.Combo(ports, key='Device-Port',
                 default_value='Unselected', expand_x=200),
    ]

    # Left Bottom Frame
    widet_analysis = [
        sg.Text('Destination'),
        sg.Combo('ThirdArm', default_value='ThirdArm', expand_x=200),
    ]

    # Right Top Frame
    widet_osc_ip = [
        sg.Text('IP'),
        sg.Input('127.0.0.1', key='OSC-IP', enable_events=True,
                 justification='r', expand_x=200),
    ]

    widet_osc_port = [
        sg.Text('Port'),
        sg.Input('9000', key='OSC-Port', enable_events=True,
                 justification='r', expand_x=200),
    ]

    # Right Bottom Frame
    widet_midi = [
        sg.Text('Port'),
        sg.Input('9000', key='Midi-Port', enable_events=True,
                 justification='r', expand_x=200),
    ]

    # Left Frame Layout
    frame_1 = [
        [sg.Frame(' 1. VRChat MIDI ', [
            widet_midi,
              [sg.Button('OFF', key="-Midi-Start-", expand_x=200,
                         button_color='white on red')],
              [sg.StatusBar('MIDI Status', expand_x=200)],
        ], size=(180, 120), expand_x=200, expand_y=200)],
        [sg.Frame(' 2. VRChat OSC ', [
            widet_osc_ip,
            widet_osc_port,
            [sg.Button('ON', key="-OSC-Start-", expand_x=200,
                       button_color='white on green')],
            [sg.StatusBar('OSC Status', expand_x=200)],
        ], size=(180, 120), expand_x=200, expand_y=200)],
    ]

    # Right Frame Layout
    frame_2 = [
        [sg.Frame(' 3. EEG Device ', [
            widet_device,
            [sg.Button('Connect', key="-Connect-", expand_x=200,
                       button_color='white on green')],
            [sg.StatusBar('Device Status', key="Device-Status", expand_x=200)],
        ], size=(180, 120), expand_x=200, expand_y=200)],
        [sg.Frame(' 4. Measurement ', [
            widet_analysis,
            [sg.Button('Utility Freq: 50Hz', key="-Power-", expand_x=200)],
            [sg.Button('Execute', key="-Execute-", expand_x=200,
                       button_color='white on blue')],
            [sg.StatusBar('Measurement Status', expand_x=200)],
        ], size=(180, 120), expand_x=200, expand_y=200)],
    ]

    # Window Layout
    layout = [
        [sg.Menu(menu_def, tearoff=False)],
        [
            # frame_1とframe_2のColumnを左右で均等に並べる
            sg.Column(frame_1, expand_x=200, expand_y=400),
            sg.Column(frame_2, expand_x=200, expand_y=400)
        ]
    ]

    # Window Setting
    window = sg.Window(
        'EEGIRL Controller',
        layout,
        size=(420, 300),
        default_button_element_size=(12, 1),
        auto_size_buttons=False,
        keep_on_top=False,
    )

    # Event Loop
    while True:
        event, values = window.read()
        if event in (None, 'Exit'):
            break
        if event == 'OSC-IP' and values['OSC-IP'] and values['OSC-IP'][-1] not in ('0123456789.'):
            window['OSC-IP'].update(values['OSC-IP'][:-1])
        if event == 'OSC-Port' and values['OSC-Port'] and values['OSC-Port'][-1] not in ('0123456789'):
            window['OSC-Port'].update(values['OSC-Port'][:-1])
        if event == 'Midi-Port' and values['Midi-Port'] and values['Midi-Port'][-1] not in ('0123456789'):
            window['Midi-Port'].update(values['Midi-Port'][:-1])
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break

        # Featrue of keeping on top
        if event == 'Top':
            window.TKroot.wm_attributes("-topmost", 1)
        elif event == 'Clear':
            window.TKroot.wm_attributes("-topmost", 0)

        # Enable to OSC connect device
        if event == '-OSC-Start-':
            down_osc = not down_osc
            window['-OSC-Start-'].update(text='ON' if down_osc else 'OFF', button_color='white on green' if down_osc else 'white on red')
            if switch_code & 1:
                switch_code &= ~1
            else:
                switch_code |= 1

        # Enable to Midi connect device
        if event == '-Midi-Start-':
            down_mid = not down_mid
            window['-Midi-Start-'].update(text='ON' if down_mid else 'OFF', button_color='white on green' if down_mid else 'white on red')
            if switch_code & 2:
                switch_code &= ~2
            else:
                switch_code |= 2

        # Enable to change utility frequency
        if event == '-Power-':
            down_pow = not down_pow
            window['-Power-'].update(
                text='Utility Freq: 50Hz' if down_pow else 'Utility Freq: 60Hz')
            if switch_code & 4:
                switch_code &= ~4
            else:
                switch_code |= 4

        # Enable to connect EEG device
        if event == '-Connect-':
            # Push Connect button
            if down_con == True:
                # Connect EEG device
                try:
                    device = values['Device-Port']
                    message, serial_port, toggle_connect = connect_port.connect_port(device)
                    window['Device-Status'].update(message)
                except:
                    window['Device-Status'].update("Error: Not Connected")
                finally:
                    pass
            # Push Disconnect button
            else:
                # Disconnect EEG device
                try:
                    serial_port.close()
                    window['Device-Status'].update(serial_port + ": Closed")
                except:
                    window['Device-Status'].update("Error: Not Closed")
            down_con = not down_con
            window['-Connect-'].update(text='Connect' if down_con else 'Disconnect', button_color='white on green' if down_con else 'white on red')

        # Enable to execute measurement
        if event == '-Execute-':
            if toggle_connect == True:
                print('mode: ' + switch_code.__str__())
                osc_ip = values['OSC-IP']
                osc_port = values['OSC-Port']
                midi_port = values['Midi-Port']
                process_ssvep.read_eeg_stream(serial_port, osc_ip, osc_port, midi_port, switch_code)
            else:
                print("Not Execute")

    window.close()

if __name__ == '__main__':
    main()

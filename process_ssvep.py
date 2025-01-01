import time
import threading
import argparse
import numpy as np
import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
import mne
from mne import create_info
from mne.filter import filter_data
from mne_realtime import LSLClient
from pythonosc import udp_client
import mido

# Set up MNE info
def setup_midi_output(midi_port):
    try:
        midi_output = mido.open_output(midi_port)
        return midi_output
    except Exception as e:
        print(f"Error opening MIDI output port: {e}" + "[Error Point: " + setup_midi_output.__name__ + "]")
        return None

# Set up OSC client
def settings_client(ip, port):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="172.19.224.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
    args = parser.parse_args()

    if ip != "":
        osc_ip = ip
    else:
        osc_ip = args.ip

    if port != "":
        osc_port = port
    else:
        osc_port = args.port

    try:
        osc_client = udp_client.SimpleUDPClient(osc_ip, int(osc_port))
        return osc_client
    except Exception as e:
        print(f"Error opening OSC client: {e}" + "[Error Point: " + settings_client.__name__ + "]")
        return None

# Process SSVEP calculation
def ssvep_thread(stop_event, board, sampling_rate, osc_ip, osc_port, midi_port, switch_code):

    # Set up MNE info
    ch_names = ['FP1', 'FP2', 'C5', 'C6', 'P7', 'P8', 'O1', 'O2']
    ch_types = ['eeg'] * len(ch_names)

    # Set the powerline frequency (Japan: 50 or 60 Hz)
    if not switch_code & 4:
        # Kanto's Power frequency is 50Hz
        powerline_freq = 50
    else:
        # Kansai's Power frequency is 60Hz
        powerline_freq = 60

    info = create_info(ch_names=ch_names, ch_types=ch_types,
                       sfreq=sampling_rate)
    montage = mne.channels.make_standard_montage('standard_1020')
    info.set_montage(montage, match_case=False)

    # Set up OSC client
    if not switch_code & 1:
        osc_client = settings_client(osc_ip, osc_port)
        try:
            osc_client.send_message("/avatar/parameters/EEGIRL_Grab", int(0))
        except Exception as e:
            print(f"Error sending OSC message: {e}" + "[Error Point: " + ssvep_thread.__name__ + "]")
            return

    # Set up MIDI output port
    if not switch_code & 2:
        midi_output = setup_midi_output(midi_port)
        if midi_output is None:
            print("MIDI output port setup failed")
            return

    # Set up SSVEP frequencies and output amplitude
    f_base = 120
    freqs = [f_base/3, f_base/5, f_base/6, f_base/8, f_base/9, f_base/11, f_base/12, f_base/14]

    # Set up SNR calculation parameters
    noise = [f_base/4, f_base/7, f_base/10, f_base/13]

    # Set up filter parameters
    l_freq = 6.0 # Update the low-frequency cutoff for high-pass filtering
    h_freq = 40.0  # Update the high-frequency cutoff for low-pass filtering

    # SSVEP detection threshold
    threshold = 0.5
    tolerance = 1e-2

    board.prepare_session()
    board.start_stream()
    data = board.get_board_data()

    if not switch_code & 1:
        osc_client.send_message("/avatar/parameters/EEGIRL_Grab", int(1))

    time.sleep(4)

    while not stop_event.is_set():
        # The number of acquired data follows the default value of 256 for n_fft
        n_fft = 256

        # Get data from BrainFlow board
        data = board.get_current_board_data(n_fft*2)
        eeg_data = data[0:n_fft, :]

        # zero-padding
        if eeg_data.shape[0] < n_fft:
            eeg_data = np.pad(
                eeg_data, (0, n_fft - eeg_data.shape[0]), 'constant')

        # Apply Common Average Reference (CAR)
        eeg_data = eeg_data - np.mean(eeg_data, axis=0)

        # Filter data
        filtered_data = filter_data(
            eeg_data, sampling_rate, l_freq, h_freq, fir_design='firwin')

        # Remove powerline noise using notch filter
        filtered_data = mne.filter.notch_filter(
            filtered_data, sampling_rate, powerline_freq, notch_widths=2)

        # Calculate power spectral density
        psd, freqs_psd = mne.time_frequency.psd_array_welch(
            filtered_data, sfreq=sampling_rate, fmin=l_freq, fmax=h_freq)

        # Initialize SSVEP power and noise power
        ssvep_power = np.zeros(len(freqs))
        noise_power = np.zeros(len(noise))

        # Calculate the SSVEP power
        for i, freq in enumerate(freqs):
            index = np.where(np.abs(freqs_psd - freq) < tolerance)
            if len(index[0]) == 0:
                print(f"No matching index found for freq: {freq}")
            else:
                ssvep_power[i] = np.sum(psd[:, index])

        # Calculate noise power
        for i, freq in enumerate(noise):
            index = np.where(np.abs(freqs_psd - freq) < tolerance)
            if len(index[0]) == 0:
                print(f"No matching index found for freq: {freq}")
            else:
                noise_power[i] = np.sum(psd[:, index])

        # Calculate SNR
        if np.sum(noise_power) > 0:
            snr = np.sum(ssvep_power) / np.sum(noise_power)
        else:
            snr = 0

        # Find the index of the SSVEP frequency with the highest power
        max_ssvep_index = np.argmax(ssvep_power)

        # Output SSVEP signal when switch_code is not 1 (OSC ON)
        if not switch_code & 1:
            # Check if the highest SSVEP power is above the threshold
            if ssvep_power[max_ssvep_index] >= threshold:
                osc_value = int(16 * max_ssvep_index)
                osc_client.send_message(
                    "/avatar/parameters/EEGIRL_Direction", osc_value)
            else:
                osc_client.send_message(
                    "/avatar/parameters/EEGIRL_Direction", int(0))

            # Output SNR signal
            osc_client.send_message(
                "/avatar/parameters/EEGIRL_Multiplication", snr)
            osc_client.send_message("/avatar/parameters/EEGIRL_Grab", int(0))
            osc_client.send_message("/avatar/parameters/EEGIRL_Grab", int(100))

        # Output SSVEP signal when switch_code is not 2 (MIDI ON)
        if not switch_code & 2:
            # Send MIDI message for max_ssvep_index
            max_midi_value = int(16 * max_ssvep_index)
            midi_output.send(mido.Message('control_change', control=1, value=max_midi_value))

            # Send MIDI message for snr
            # Scale SNR value to the MIDI range [0, 30]
            snr_midi_value = int(snr * 30)
            midi_output.send(mido.Message('control_change', control=2, value=snr_midi_value))

        # The acquisition interval is set to the inverse of the sampling rate (1/250 = 0.004s)
        time.sleep(256 * (1 / sampling_rate))

# Set up BrainFlow board
def setup_bci_device(serial_port):
    try:
        # Set up BrainFlow board
        board_id = BoardIds.CYTON_BOARD.value
        params = BrainFlowInputParams()
        params.serial_port = serial_port

        board = BoardShim(board_id, params)
        sampling_rate = BoardShim.get_sampling_rate(board_id)
    except Exception as e:
        print("Error in setup_bci_device:", e)
        raise

    return board, sampling_rate

# Set up MNE info
def read_eeg_stream(serial_port, osc_ip, osc_port, midi_port, switch_code):
    # Set up BrainFlow board
    board, sampling_rate = setup_bci_device(serial_port)

    # Start SSVEP thread
    stop_event = threading.Event()
    ssvep_t = threading.Thread(target=ssvep_thread, args=(stop_event, board, sampling_rate, osc_ip, osc_port, midi_port, switch_code))
    ssvep_t.start()

    # Main thread sleep
    time.sleep(60)

    # Stop SSVEP thread
    stop_event.set()
    ssvep_t.join()

    board.stop_stream()
    board.release_session()

# Main block for stand-alone operation (for debugging)
if __name__ == '__main__':
    # Set to custom values for your own use, please.
    serial_port = "COM4"
    osc_ip = "192.168.1.100"
    osc_port = 9000
    midi_port = 0
    switch_code = 0
    read_eeg_stream(serial_port, osc_ip, osc_port, midi_port, switch_code)

import pyaudio
import logging

def get_audio_devices():
    """Get lists of available audio input and output devices."""
    try:
        p = pyaudio.PyAudio()
        input_devices = []
        output_devices = []
        
        # Iterate through all audio devices
        for i in range(p.get_device_count()):
            try:
                device_info = p.get_device_info_by_index(i)
                
                # Create a simplified device info dictionary
                device = {
                    'index': i,
                    'name': device_info['name'],
                    'maxInputChannels': device_info['maxInputChannels'],
                    'maxOutputChannels': device_info['maxOutputChannels'],
                    'defaultSampleRate': int(device_info['defaultSampleRate'])
                }
                
                # Categorize as input or output device
                if device['maxInputChannels'] > 0:
                    input_devices.append(device)
                if device['maxOutputChannels'] > 0:
                    output_devices.append(device)
                    
            except Exception as e:
                logging.error(f"Error getting info for device {i}: {str(e)}")
                continue
        
        p.terminate()
        return input_devices, output_devices
        
    except Exception as e:
        logging.error(f"Error initializing PyAudio: {str(e)}")
        return [], []

def find_device_by_name(devices, name):
    """Find a device in the list by its name."""
    for device in devices:
        if device['name'] == name:
            return device
    return None

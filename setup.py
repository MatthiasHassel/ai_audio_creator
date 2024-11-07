from setuptools import setup, find_packages

setup(
    name='ai_audio_creator',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'customtkinter==5.2.2',
        'tkinterdnd2==0.3.0',
        'pydub==0.25.1',
        'soundfile==0.12.1',
        'pygame==2.6.0',
        'pyaudio==0.2.13',
        'sounddevice==0.4.7',
        'openai==1.37.1',
        'elevenlabs==1.3.1',
        'numpy==2.0.1',
        'PyYAML==6.0.1',
        'PyPDF2==3.0.1',
        'requests==2.32.3',
        'python-dotenv==1.0.1',
        'python-reapy==0.10.0',
    ],
    entry_points={
        'console_scripts': [
            'ai_audio_creator=main:main',
        ],
    },
)
from setuptools import setup, find_packages

setup(
    name='ai_audio_creator',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'tkinter',
        'requests',
        'elevenlabs',
        'python-dotenv',
        'PyYAML',
    ],
    entry_points={
        'console_scripts': [
            'ai_audio_creator=main:main',
        ],
    },
)
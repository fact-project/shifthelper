from setuptools import setup

setup(
    name='shifthelper',
    version='0.7.0',
    description='a tool for helping people with a FACT night shift',
    url='https://github.com/fact-project/shifthelper',
    author='Dominik Neise, Maximilian Noethe, Sebastian Mueller',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=[
        'shifthelper',
        'shifthelper.checks',
        'shifthelper.cli',
        'shifthelper.communication',
        'shifthelper.tools',
        ],
    install_requires=[
        'pandas',           # in anaconda
        'requests',         # in anaconda
        'numpy',            # in anaconda
        'matplotlib>=1.4',  # in anaconda
        'python-dateutil',  # in anaconda
        'sqlalchemy',       # in anaconda
        'PyMySQL',          # in anaconda
        'pytz',             # in anaconda
        'blessings',
        'twilio',
        'docopt',           # in anaconda
        'numexpr',
        'smart_fact_crawler==0.2.1',
        'retrying'
    ],
    entry_points={'console_scripts': [
        'shifthelper = shifthelper.__main__:main',
        'qlabot = shifthelper.qlabot:main',
        'fact_ircam = shifthelper.tools.ircam:main',
        'fact_call = shifthelper.tools.call:main',
    ]},
    zip_safe=False,
)

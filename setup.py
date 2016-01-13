from distutils.core import setup

setup(
    name='fact_shift_helper',
    version='0.3.4',
    description='a tool for helping people with a FACT night shift',
    url='https://bitbucket.org/dneise/fact_shift_helper',
    author='Dominik Neise, Maximilian Noethe, Sebastian Mueller',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=[
        'fact_shift_helper',
        'fact_shift_helper.checks',
        'fact_shift_helper.cli',
        'fact_shift_helper.communication',
        'fact_shift_helper.tools',
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
    ],
    scripts=['scripts/shift_helper', 'scripts/qla_bot'],
    package_data={'fact_shift_helper.tools': ['config.gpg']},
    zip_safe=False
)

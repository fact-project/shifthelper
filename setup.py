from distutils.core import setup, Extension

setup(
    name='fact_shift_helper',
    version='0.1',
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
        'fact_shift_helper.unused',
        ],
    install_requires=[
        'requests',         # 2.7.0 is in anaconda
        'scikit-image',     # 0.11.3 is in anaconda
        'numpy',            # 1.9.2 is in anaconda
        'scipy',            # 0.15.1 is in anaconda
        'matplotlib>=1.4',  # 1.4.3 is in anaconda
        'python-dateutil',  # 2.4.2 is in anaconda
        'pymongo>=2.7',     # 2.8 is in anaconda
        'pandas',           # 0.16.2 is in anaconda
        'sqlalchemy',       # 1.0.5 is in anaconda
        'PyMySQL',          # 0.6.6 is in anaconda
        'pytz',             # 2015.4 is in anaconda
        'blessings',
        'twilio',
    ],
    scripts=['scripts/shift_helper.py'],
    package_data={'fact_shift_helper': ['config.gpg']},
    zip_safe=False
)
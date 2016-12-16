from setuptools import setup

setup(
    name='shifthelper',
    version='1.0.1',
    description='a tool for helping people with a FACT night shift',
    url='https://github.com/fact-project/shifthelper',
    author='Dominik Neise, Maximilian Noethe, Sebastian Mueller',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=[
        'shifthelper',
        'shifthelper.tools',
        'shifthelper.db_cloner',
    ],
    package_data={
        'shifthelper.db_cloner': ['logging.conf'],
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest>=3.0.0'],
    install_requires=[
        'pandas',           # in anaconda
        'requests',         # in anaconda
        'numpy',            # in anaconda
        'matplotlib>=1.5',  # in anaconda
        'python-dateutil',  # in anaconda
        'sqlalchemy',       # in anaconda
        'PyMySQL',          # in anaconda
        'pytz',             # in anaconda
        'twilio',
        'numexpr',
        'smart_fact_crawler==0.2.1',
        'custos==0.0.5',
        'pyfact==0.8.2',
        'retrying',
        'wrapt',
        'python-json-logger',
        'telepot',
    ],
    entry_points={'console_scripts': [
        'shifthelper = shifthelper.__main__:main',
        'shifthelper_db_cloner = shifthelper.db_cloner.__main__:main',
    ]},
    zip_safe=False,
)

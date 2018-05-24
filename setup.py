from setuptools import setup

setup(
    name='shifthelper',
    version='1.5.0',
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
    tests_require=['pytest>=3.0.0', 'freezegun'],
    install_requires=[
        'pandas==0.22.0',
        'numpy==1.14.1',
        'twilio==5.7.0',
        'requests',
        'python-dateutil',
        'sqlalchemy',
        'PyMySQL',
        'pytz',
        'numexpr',
        'smart_fact_crawler==0.6.0',
        'custos==0.0.7',
        'retrying',
        'wrapt',
        'python-json-logger',
        'telepot',
        'cachetools',
    ],
    entry_points={'console_scripts': [
        'shifthelper = shifthelper.__main__:main',
        'shifthelper_db_cloner = shifthelper.db_cloner.__main__:main',
    ]},
    zip_safe=False,
)

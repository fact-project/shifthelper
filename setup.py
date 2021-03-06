from setuptools import setup

setup(
    name='shifthelper',
    version='1.7.0',
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
    python_requires='>=3.6.0',
    setup_requires=['pytest-runner'],
    tests_require=['pytest>=3.0.0', 'freezegun'],
    install_requires=[
        'pandas~=0.22.0',
        'numpy==1.14.1',
        'requests',
        'python-dateutil',
        'sqlalchemy',
        'PyMySQL',
        'pytz',
        'numexpr',
        'smart_fact_crawler @ https://github.com/fact-project/smart_fact_crawler/archive/v0.6.4.tar.gz',
        'custos[all]==0.1.1',
        'retrying',
        'wrapt',
        'python-json-logger',
        'cachetools',
    ],
    entry_points={'console_scripts': [
        'shifthelper = shifthelper.__main__:main',
        'shifthelper_db_cloner = shifthelper.db_cloner.__main__:main',
    ]},
    zip_safe=False,
)

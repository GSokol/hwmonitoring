"""A setuptools based setup module.

See: https://github.com/pypa/sampleproject/blob/master/setup.py
"""

from setuptools import setup, find_packages

REQUIRES = [
    'aiohttp==3.7.3',
    'aiokafka==0.7.0',
    'asyncpg==0.21.0',
    'envparse==0.2.0',
    'PyYAML==5.3.1',
]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    author='Grigorii Sokolik',
    author_email='g.sokol99@g-sokol.info',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking'
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    description='Simple http monitoring solution.',
    entry_points={
        'console_scripts': [
            'hw-monitoring-scraper = hwmonitoring.cmd.scraper:main',
            'hw-monitoring-persister = hwmonitoring.cmd.persister:main',
        ],
    },
    install_requires=REQUIRES,
    keywords='monitoring, kafka, postgres, aiven',
    long_description=long_description,
    long_description_content_type='text/markdown',
    name='hwmonitoring',
    packages=find_packages(exclude='tests'),
    url='https://github.com/GSokol/hwmonitoring',
    version='0.0.1',
)

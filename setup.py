from setuptools import setup

setup(
    name='ControlsTracker',
    version='0.1.0',
    py_modules=['control'],
    install_requires=[
        'Click', 'PyYAML', 'alembic', 'xlrd', 'XlsxWriter', 'xlwt', 'pandas', 'plotly', 'sqlalchemy'
    ],
    entry_points={
        'console_scripts': [
            'controls_run = controls:cli',
        ],
    },
)
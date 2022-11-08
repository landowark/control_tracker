from setuptools import setup

setup(
    name='ControlsTracker',
    version='0.1.0',
    py_modules=['controls'],
    install_requires=[
        'Click', 'PyYAML', 'alembic', 'xlrd', 'XlsxWriter', 'xlwt', 'pandas', 'plotly', 'sqlalchemy', 'zipp', 'openpyxl'
    ],
    entry_points={
        'console_scripts': [
            'controls = controls.__main__:cli',
            'controls_db_init = controls.setup:run_alembic_upgrade'
        ],
    },
)
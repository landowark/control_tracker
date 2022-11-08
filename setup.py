from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        import alembic.config
        alembicArgs = [
            '--raiseerr',
            'upgrade', 'head',
        ]
        print("Running Alembic migrations...")
        alembic.config.main(argv=alembicArgs)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        import alembic.config
        alembicArgs = [
            '--raiseerr',
            'upgrade', 'head',
        ]
        print("Running Alembic migrations...")
        alembic.config.main(argv=alembicArgs)
        

setup(
    name='ControlsTracker',
    version='0.1.0',
    py_modules=['controls'],
    install_requires=[
        'Click', 'PyYAML', 'alembic', 'xlrd', 'XlsxWriter', 'xlwt', 'pandas', 'plotly', 'sqlalchemy', 'zipp', 'openpyxl'
    ],
    entry_points={
        'console_scripts': [
            'controls = ControlsTracker.__main__:cli',
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
)
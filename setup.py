from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
import alembic.config

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
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
        'Click', 'PyYAML', 'alembic', 'xlrd', 'XlsxWriter', 'xlwt', 'pandas', 'plotly', 'sqlalchemy', 'zipp'
    ],
    entry_points={
        'console_scripts': [
            'controls = controls.__main__:cli',
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
)
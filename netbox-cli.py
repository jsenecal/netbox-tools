#! /usr/bin/env python3

from cryptography.fernet import Fernet, InvalidToken
from clint import resources
import binascii
import click
import click_log
import os
import sys
import configparser
import click
import pynetbox
import json
import logging
logger = logging.getLogger(__name__)
click_log.basic_config(logger)


resources.init('connectit', 'netbox-cli')

config = configparser.ConfigParser()


def write_config():
    try:
        with resources.user.open('config.ini', mode='w') as configFile:
            config.write(configFile)
    except IOError:
        pass


class ContextObject:
    def __init__(self, ctx):
        self.ctx = ctx
        self.secret = None
        self.fernet = None

    def validate_secret(self):
        if not self.secret:
            self.secret = click.prompt(
                "Enter Configuration Secret Key", hide_input=True)
            self.fernet = Fernet(self.secret.encode())

        if not config['global']['secret']:
            logger.error("The secret key is not set in the configuration file")
            sys.exit(400)
        else:
            try:
                self.decrypt(config['global']['secret'])
            except InvalidToken:
                logger.error("The secret key is invalid")
                sys.exit(403)

    def decrypt(self, string):
        return self.fernet.decrypt(string.encode())

    def encrypt(self, string):
        return self.fernet.encrypt(string.encode())

    @property
    def netbox_token(self):
        return self.decrypt(config['netbox']['token'])

    @netbox_token.setter
    def netbox_token(self, value):
        config['netbox']['token'] = obj.encrypt(token).decode()
        write_config()

class OptionPromptNull(click.Option):
    _value_key = '_default_val'

    def get_default(self, ctx):
        if not hasattr(self, self._value_key):
            default = super(OptionPromptNull, self).get_default(ctx)
            setattr(self, self._value_key, default)
        return getattr(self, self._value_key)

    def prompt_for_value(self, ctx):
        default = self.get_default(ctx)

        # only prompt if the default value is None
        if default is None:
            return super(OptionPromptNull, self).prompt_for_value(ctx)

        return default


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


@click.command(cls=AliasedGroup)
@click.option('--secret', help='Secret key to encrypt sensible data with',
              envvar='CONFIG_SECRET', show_envvar=True)
@click.pass_context
def cli(ctx, secret):
    ctx.obj = ContextObject(ctx)
    ctx.obj.secret = secret

    config['netbox'] = {
        'uri': '',
        'private_key_file': '',
        'token': ''
    }

    config['global'] = {
        'secret': '',
    }

    try:
        with resources.user.open('config.ini', mode='r') as configFile:
            config.read_file(configFile)
    except IOError:
        pass

    if ctx.obj.secret:
        try:
            ctx.obj.fernet = Fernet(ctx.obj.secret.encode())
        except binascii.Error:
            logger.error("The secret key is not in Base64 format")
            ctx.exit(401)


# config
@cli.command(name='config', cls=AliasedGroup)
def configuration():
    pass

# config validate-secret
@configuration.command(name='validate-secret')
@click.pass_obj
def config_validate_secret(obj):
    obj.validate_secret()

# config generate-secret
@configuration.command(name='generate-secret')
def config_generate_secret():
    click.confirm(
        'This will generate a new secret and configuration file. Continue?', abort=True)
    key = Fernet.generate_key()
    fernet = Fernet(key)
    config['global'] = {
        'secret': fernet.encrypt(key).decode(),
    }
    config.remove_section('netbox')
    write_config()
    click.echo("New secret key: %s" % key.decode())
    click.echo("Please store this in a secure location")


# config get
@configuration.command(name='get', cls=AliasedGroup)
@click.pass_obj
def config_get(obj):
    obj.validate_secret()


@config_get.command(name='netbox-uri')
def get_netbox_uri():
    if config['netbox']['uri']:
        click.echo(config['netbox']['uri'])
    else:
        click.echo("NOT SET")


@config_get.command(name='netbox-private-key-file')
def get_netbox_private_key_file():
    if config['netbox']['private_key_file']:
        click.echo(config['netbox']['private_key_file'])
    else:
        click.echo("NOT SET")


@config_get.command(name='netbox-token')
@click.pass_obj
def get_netbox_token(obj):
    if obj.netbox_token:
        click.echo(obj.netbox_token)
    else:
        click.echo("NOT SET")

# config set
@configuration.command(name='set', cls=AliasedGroup)
@click.pass_obj
def config_set(obj):
    obj.validate_secret()


@config_set.command(name='netbox-uri')
@click.argument('value')
def set_netbox_uri(value):
    config['netbox']['uri'] = value
    write_config()
    click.echo('netbox-uri set to: {}'.format(config['netbox']['uri']))


@config_set.command(name='netbox-private-key-file')
@click.argument('file', type=click.Path(exists=True))
def set_netbox_private_key_file(file):
    config['netbox']['private_key_file'] = file
    write_config()
    click.echo(
        'netbox-private-key-file set to: {}'.format(config['netbox']['private_key_file']))


@config_set.command(name='netbox-token')
@click.pass_obj
def set_netbox_token(obj):
    token = click.prompt('Token')
    obj.netbox_token = token
    click.echo('netbox-token set')


if __name__ == '__main__':
    cli(auto_envvar_prefix='NETBOX_CLI')

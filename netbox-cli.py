import click
import click_log
import os
import sys
import configparser
import click
import pynetbox
import json
import bcrypt
import logging
logger = logging.getLogger(__name__)
click_log.basic_config(logger)

from clint import resources

resources.init('connectit', 'netbox-cli')

config = configparser.ConfigParser()

def write_config():
        try:
            with resources.user.open('config.ini', mode='w') as configFile:
                config.write(configFile)
        except IOError:
            pass

def get_hash(value, secret):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(value + salt + secret, salt)

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
@click.option('--secret', help='Secret key to encrypt sensible data with')
@click.pass_context
def cli(ctx, secret):
    ctx.obj = dict()
    ctx.obj['secret'] = secret
    
    config['netbox'] = {
        'uri': '',
        'private_key_file': '',
        'token': ''
    }
    config['netconf'] = {}

    try:
        with resources.user.open('config.ini', mode='r') as configFile:
                config.read_file(configFile)
    except IOError:
        pass


# config
@cli.command(name='config', cls=AliasedGroup)
def configuration():
    pass

## config get
@configuration.command(name='get', cls=AliasedGroup)
def config_get():
    pass

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
def get_netbox_token():
    if config['netbox']['token']:
        click.echo(config['netbox']['token'])
    else:
        click.echo("NOT SET")

## config set
@configuration.command(name='set', cls=AliasedGroup)
def config_set():
    pass

@config_set.command(name='netbox-uri')
@click.argument('value')
def set_netbox_uri(value):
    config['netbox']['uri']=value
    write_config()
    click.echo('netbox-uri set to: {}'.format(config['netbox']['uri']))

@config_set.command(name='netbox-private-key-file')
@click.argument('file', type=click.Path(exists=True))
def set_netbox_private_key_file(file):
    config['netbox']['private_key_file']=file
    write_config()
    click.echo('netbox-private-key-file set to: {}'.format(config['netbox']['private_key_file']))

@config_set.command(name='netbox-token')
@click.pass_context
def set_netbox_token(ctx):
    token = click.prompt('Token')
    config['netbox']['token']=get_hash(token, ctx.obj['secret'])
    write_config()
    click.echo('netbox-token set')


if __name__ == '__main__':
    cli()
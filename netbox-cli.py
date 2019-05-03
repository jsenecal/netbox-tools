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
        self._netbox = None

        config['netbox'] = {
            'uri': '',
            'private_key_file': '',
            'token': ''
        }

        config['arin'] = {
            'uri': '',
            'token': '',
            'parent_org_handle': ''
        }

        config['global'] = {
            'secret': '',
        }

        try:
            with resources.user.open('config.ini', mode='r') as configFile:
                config.read_file(configFile)
        except IOError:
            pass

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
        return self.decrypt(config['netbox']['token']).decode()

    @netbox_token.setter
    def netbox_token(self, value):
        config['netbox']['token'] = self.encrypt(value).decode()
        write_config()

    @property
    def netbox_uri(self):
        return config['netbox']['uri']

    @netbox_uri.setter
    def netbox_uri(self, value):
        config['netbox']['uri'] = value
        write_config()

    @property
    def netbox_private_key_file(self):
        return config['netbox']['private_key_file']

    @netbox_private_key_file.setter
    def netbox_private_key_file(self, value):
        config['netbox']['private_key_file'] = value
        write_config()

    @property
    def arin_token(self):
        return self.decrypt(config['arin']['token']).decode()

    @arin_token.setter
    def arin_token(self, value):
        config['arin']['token'] = self.encrypt(value).decode()
        write_config()

    @property
    def arin_uri(self):
        return config['arin']['uri']

    @arin_uri.setter
    def arin_uri(self, value):
        config['arin']['uri'] = value
        write_config()

    @property
    def arin_parent_org_handle(self):
        return config['arin']['parent_org_handle']

    @arin_parent_org_handle.setter
    def arin_parent_org_handle(self, value):
        config['arin']['parent_org_handle'] = value
        write_config()

    @property
    def netbox(self):
        if self._netbox is None:
            logger.debug('netbox context object is not defined')
            self._netbox = pynetbox.api(
                self.netbox_uri,
                token=self.netbox_token,
                private_key_file=self.netbox_private_key_file
            )
        return self._netbox


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
@click_log.simple_verbosity_option(logger)
@click.pass_context
def cli(ctx, secret):
    ctx.obj = ContextObject(ctx)
    ctx.obj.secret = secret

    if ctx.obj.secret:
        try:
            ctx.obj.fernet = Fernet(ctx.obj.secret.encode())
        except binascii.Error:
            logger.error("The secret key is not in Base64 format")
            ctx.exit(401)

# arin
@cli.command(name='arin', cls=AliasedGroup)
def arin():
    pass

# arin reassign
@arin.command(name='reassign', cls=AliasedGroup)
def arin_reassign():
    pass

# arin reassign simple
@arin_reassign.command(name='simple')
@click.option('-a', '--aggregate_id', required=False)
@click.option('-p', '--prefix_id', required=False)
@click.option('-r', '--replace_existing', is_flag=True)
@click.pass_context
def arin_reassign_simple(ctx, aggregate_id=None, prefix_id=None, replace_existing=False):
    obj = ctx.obj
    if aggregate_id and prefix_id:
        click.echo(
            "Either '--aggregate_id' or '--prefix_id' must be specified, not both\n"
        )
        click.echo(ctx.get_help())
        ctx.exit(1)

    if aggregate_id is None and prefix_id is None:
        aggregates = obj.netbox.ipam.aggregates.all()
        choices = [str(aggregate.id) for aggregate in aggregates]

        for aggregate in aggregates:
            aid = str(aggregate.id)
            click.echo("[{aid}]: {aggregate}".format(
                aggregate=aggregate,
                aid=aid.rjust(4-len(aid)))
            )
        choice = click.prompt(
            "Reassign subnets in which aggregate?",
            type=click.Choice(choices)
        )
        aggregate_id = int(choice)
        
    if aggregate_id and prefix_id is None:
        aggregate = obj.netbox.ipam.aggregates.get(aggregate_id)
        prefixes = obj.netbox.ipam.prefixes.filter(within_include=aggregate)
        for prefix in prefixes:
            if not replace_existing and prefix.custom_fields['RIR NET Handle']:
                logger.debug(
                    "%s already has an RIR NET Handle, skipping" % prefix)
                continue

            ctx.invoke(arin_reassign_simple, prefix_id=prefix.id, replace_existing=replace_existing)

    if prefix_id and not aggregate_id:
        # Get the prefix
        prefix=obj.netbox.ipam.prefixes.get(prefix_id)
        # Query the hyperlinked endpoints
        prefix.tenant.full_details()
        prefix.site.full_details()
        prefix.tenant.full_details()
        site = prefix.site
        tenant = prefix.tenant

        logger.info("Processing {prefix}@{site} for {tenant}".format(
            prefix=prefix,
            site=site,
            tenant=tenant
        ))


        if not replace_existing and prefix.custom_fields['RIR NET Handle']:
            logger.debug(
                "%s already has an RIR NET Handle, skipping" % prefix)
            return
        # Build ARIN Cust Payload
    import ipdb
    ipdb.set_trace()

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
def get_netbox_uri(obj):
    if obj.netbox_uri:
        click.echo(obj.netbox_uri)
    else:
        click.echo("NOT SET")


@config_get.command(name='netbox-private-key-file')
@click.pass_obj
def get_netbox_private_key_file(obj):
    if obj.netbox_private_key_file:
        click.echo(obj.netbox_private_key_file)
    else:
        click.echo("NOT SET")


@config_get.command(name='netbox-token')
@click.pass_obj
def get_netbox_token(obj):
    if obj.netbox_token:
        click.echo(obj.netbox_token)
    else:
        click.echo("NOT SET")

@config_get.command(name='arin-uri')
def get_arin_uri(obj):
    if obj.arin_uri:
        click.echo(obj.arin_uri)
    else:
        click.echo("NOT SET")


@config_get.command(name='arin-parent-org-handle')
@click.pass_obj
def get_arin_parent_org_handle(obj):
    if obj.arin_private_key_file:
        click.echo(obj.arin_private_key_file)
    else:
        click.echo("NOT SET")


@config_get.command(name='arin-token')
@click.pass_obj
def get_arin_token(obj):
    if obj.arin_token:
        click.echo(obj.arin_token)
    else:
        click.echo("NOT SET")

# config set
@configuration.command(name='set', cls=AliasedGroup)
@click.pass_obj
def config_set(obj):
    obj.validate_secret()


@config_set.command(name='netbox-uri')
@click.argument('value')
@click.pass_obj
def set_netbox_uri(obj, value):
    obj.netbox_uri = value
    click.echo('netbox-uri set to: {}'.format(config['netbox']['uri']))


@config_set.command(name='netbox-private-key-file')
@click.argument('file', type=click.Path(exists=True))
@click.pass_obj
def set_netbox_private_key_file(obj, file):
    obj.netbox_private_key_file = file
    click.echo(
        'netbox-private-key-file set to: {}'.format(config['netbox']['private_key_file']))


@config_set.command(name='netbox-token')
@click.pass_obj
def set_netbox_token(obj):
    token = click.prompt('Token')
    obj.netbox_token = token
    click.echo('netbox-token set')

@config_set.command(name='arin-uri')
@click.argument('value')
@click.pass_obj
def set_arin_uri(obj, value):
    obj.arin_uri = value
    click.echo('arin-uri set to: {}'.format(config['arin']['uri']))


@config_set.command(name='arin-parent-org-handle')
@click.argument('file', type=click.Path(exists=True))
@click.pass_obj
def set_arin_parent_org_handle(obj, file):
    obj.arin_private_key_file = file
    click.echo(
        'arin-parent-org-handle set to: {}'.format(config['arin']['parent_org_handle']))


@config_set.command(name='arin-token')
@click.pass_obj
def set_arin_token(obj):
    token = click.prompt('Token')
    obj.arin_token = token
    click.echo('arin-token set')


# pylint: disable=no-value-for-parameter,unexpected-keyword-arg
if __name__ == '__main__':
    try:
        cli(auto_envvar_prefix='NETBOX_CLI')
    except pynetbox.core.query.RequestError as e:
        logger.debug(e)

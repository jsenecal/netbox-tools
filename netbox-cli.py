#! /usr/bin/env python3

from cryptography.fernet import Fernet, InvalidToken
from clint import resources
import binascii
import base64
import click
import click_log
import os
import sys
import configparser
import ipaddress
import pynetbox
import json
import logging
from tools.arin.payloads import CustomerPayload, NetPayload, NetBlockPayload, TicketedRequestPayload
from tools.arin import Arin
from tools.googlemaps import GeocodeResult
from tools.googlemaps.googlemaps import GeocodeResultError

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
        self._gmaps = None
        self._arin = None

        config['netbox'] = {
            'uri': '',
            'private_key_file': '',
            'token': ''
        }

        config['arin'] = {
            'api_key': '',
            'parent_org_handle': '',
            'uri': 'https://www.ote.arin.net/',
            'origin_ases': ''
        }

        config['google'] = {
            'api_key': '',
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
        if isinstance(string, str):
            string = string.encode()
        try:
            return base64.urlsafe_b64decode(self.fernet.decrypt(string))
        except InvalidToken:
            return bytes()

    def encrypt(self, string):
        if isinstance(string, str):
            string = string.encode()
        return self.fernet.encrypt(base64.urlsafe_b64encode(string))

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
    def arin_api_key(self):
        return self.decrypt(config['arin']['api_key']).decode()

    @arin_api_key.setter
    def arin_api_key(self, value):
        config['arin']['api_key'] = self.encrypt(value).decode()
        write_config()

    @property
    def arin_uri(self):
        return config['arin']['uri']

    @arin_uri.setter
    def arin_uri(self, value):
        config['arin']['uri'] = value
        write_config()

    @property
    def arin_origin_ases(self):
        return config['arin']['origin_ases'].split(',')

    @arin_origin_ases.setter
    def arin_origin_ases(self, value):
        config['arin']['origin_ases'] = value
        write_config()

    @property
    def arin_parent_org_handle(self):
        return config['arin']['parent_org_handle']

    @arin_parent_org_handle.setter
    def arin_parent_org_handle(self, value):
        config['arin']['parent_org_handle'] = value
        write_config()

    @property
    def google_api_key(self):
        return self.decrypt(config['google']['api_key']).decode()

    @google_api_key.setter
    def google_api_key(self, value):
        config['google']['api_key'] = self.encrypt(value).decode()
        write_config()

    @property
    def netbox(self):
        if self._netbox is None:
            self._netbox = pynetbox.api(
                self.netbox_uri,
                token=self.netbox_token,
                private_key_file=self.netbox_private_key_file
            )
            logger.debug('`netbox` context object initialized')
        else:
            logger.debug('`netbox` context object accessed')
        return self._netbox

    @property
    def gmaps(self):
        if self._gmaps is None:
            import googlemaps
            self._gmaps = googlemaps.Client(key=self.google_api_key)
            logger.debug('`gmaps` context object initialized')
        else:
            logger.debug('`gmaps` context object accessed')
        return self._gmaps

    @property
    def arin(self):
        if self._arin is None:
            self._arin = Arin(apikey=self.arin_api_key, uri=self.arin_uri)
            logger.debug('`arin` context object initialized')
        else:
            logger.debug('`arin` context object accessed')
        return self._arin


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
@click.pass_context
def arin(ctx):
    obj = ctx.obj
    if not obj.netbox_uri and not obj.netbox_token:
        click.echo(
            "netbox config settings are not properly set\n"
        )
        ctx.exit(1)

# arin reassign
@arin.command(name='reassign', cls=AliasedGroup)
def arin_reassign():
    pass

# arin reassign simple
@arin_reassign.command(name='simple')
@click.option('-a', '--aggregate-id', required=False)
@click.option('-p', '--prefix-id', required=False)
@click.option('-r', '--replace-existing', is_flag=True)
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
            if not replace_existing and prefix.custom_fields['RIR Handle']:
                logger.info(
                    "%s already has an RIR Handle, skipping" % prefix)
                continue

            if not prefix.site:
                logger.info(
                    "%s has no site, skipping" % prefix
                )
                continue
            if not prefix.tenant:
                logger.info(
                    "%s has no tenant, skipping" % prefix
                )
                continue
            ctx.invoke(arin_reassign_simple, prefix_id=prefix.id,
                       replace_existing=replace_existing)

    if prefix_id and not aggregate_id:
        parent_org_handle = obj.arin_parent_org_handle

        if not parent_org_handle:
            logger.error(
                "arin-parent-org-handle setting is not set, exitting"
            )
            ctx.exit(1)

        # Get the prefix
        prefix = obj.netbox.ipam.prefixes.get(prefix_id)

        if not replace_existing and prefix.custom_fields['RIR Handle']:
            logger.error(
                "%s already has an RIR Handle, exitting" % prefix
            )
            ctx.exit(1)

        # Get its aggregate
        aggregate = obj.netbox.ipam.aggregates.get(q=prefix)

        parent_net_handle = aggregate.custom_fields['RIR Handle']

        if not parent_net_handle:
            logger.error(
                "Aggregate `%s` has no RIR Handle, exitting" % aggregate
            )
            ctx.exit(1)

        # Query the hyperlinked endpoints
        if prefix.tenant:
            prefix.tenant.full_details()
        else:
            logger.error(
                "%s has no tenant, exitting" % prefix
            )
            ctx.exit(1)

        if prefix.site:
            site = obj.netbox.dcim.sites.get(prefix.site.id)
        else:
            logger.error(
                "%s has no site, exitting" % prefix
            )
            ctx.exit(1)

        tenant = prefix.tenant

        logger.info("Processing {prefix}@{site} for {tenant}".format(
            prefix=prefix,
            site=site,
            tenant=tenant
        ))

        # Build ARIN Cust Payload
        customer_name = tenant.name
        geocode_result = GeocodeResult(
            obj.gmaps.geocode(site.physical_address))

        iso3166_1_name = geocode_result.iso3166_1.name
        iso3166_1_code2 = geocode_result.iso3166_1.alpha_2
        iso3166_1_code3 = geocode_result.iso3166_1.alpha_3
        iso3166_1_e164 = geocode_result.iso3166_1.numeric
        street_address = geocode_result.street_address
        city = geocode_result.city
        iso3166_2 = geocode_result.short_address_components['administrative_area_level_1']
        postal_code = geocode_result.postal_code
        comment = ""
        private_customer = 'true'

        arin_customer_payload = CustomerPayload(customer_name, iso3166_1_name, iso3166_1_code2, iso3166_1_code3,
                                                iso3166_1_e164, street_address, city, iso3166_2, postal_code, comment, parent_org_handle, private_customer)

        arin_customer_response = obj.arin.create_recipient_customer(
            parent_net_handle, arin_customer_payload
        )

        if arin_customer_response:
            arin_customer_response_payload = CustomerPayload.from_xml(
                str(arin_customer_response)
            )
            if not replace_existing and prefix.custom_fields['RIR Handle']:
                logger.debug(
                    "%s already has an RIR Handle, skipping creation of the NET object" % prefix)
            else:
                ip_network = ipaddress.ip_network(prefix.prefix)

                # Build ARIN NetBlock Payload
                arin_netblock_payload = NetBlockPayload(start_address=ip_network.network_address,
                                                        description=prefix.role.name,
                                                        cidr_length=ip_network.prefixlen)

                net_name = "CUST-%s-%s" % (
                    prefix.family, "-".join(
                        str(ip_network.network_address).split('.')
                    )
                )

                # Build ARIN Net Payload
                arin_net_payload = NetPayload(version=prefix.family.value,
                                              comment=None,
                                              parent_net_handle=parent_net_handle,
                                              net_name=net_name,
                                              origin_ases=obj.arin_origin_ases,
                                              net_blocks=[
                                                  arin_netblock_payload],
                                              handle=None,
                                              registration_date=None,
                                              customer_handle=arin_customer_response_payload.handle,
                                              poc_links=None)

                arin_net_response = obj.arin.reassign_net(
                    parent_net_handle, arin_net_payload
                )
                if arin_net_response:
                    arin_net_response_payload = TicketedRequestPayload.from_xml(
                        arin_net_response)

                    prefix.custom_fields['RIR Handle'] = arin_net_response_payload.handle
                    prefix.custom_fields['RIR registration date'] = arin_net_response_payload.registration_date
                    prefix.custom_fields['RIR Net Name'] = arin_net_response_payload.net_name
                    prefix.save()
                else:
                    import ipdb; ipdb.set_trace()
        else:
            import ipdb; ipdb.set_trace()


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


@config_get.command(name='arin-parent-org-handle')
@click.pass_obj
def get_arin_parent_org_handle(obj):
    if obj.arin_private_key_file:
        click.echo(obj.arin_private_key_file)
    else:
        click.echo("NOT SET")


@config_get.command(name='arin-origin-ases')
@click.pass_obj
def get_arin_origin_ases(obj):
    if obj.arin_origin_ases:
        click.echo(obj.arin_origin_ases)
    else:
        click.echo("NOT SET")


@config_get.command(name='arin-api-key')
@click.pass_obj
def get_arin_api_key(obj):
    if obj.arin_api_key:
        click.echo(obj.arin_api_key)
    else:
        click.echo("NOT SET")


@config_get.command(name='arin-uri')
@click.pass_obj
def get_arin_uri(obj):
    if obj.arin_uri:
        click.echo(obj.arin_uri)
    else:
        click.echo("NOT SET")


@config_get.command(name='google-api-key')
@click.pass_obj
def get_google_api_key(obj):
    if obj.google_api_key:
        click.echo(obj.google_api_key)
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
    click.echo('netbox-uri set to: {}'.format(obj.netbox_uri))


@config_set.command(name='arin-uri')
@click.argument('value')
@click.pass_obj
def set_arin_uri(obj, value):
    obj.arin_uri = value
    click.echo('arin-uri set to: {}'.format(obj.arin_uri))


@config_set.command(name='netbox-private-key-file')
@click.argument('file', type=click.Path(exists=True))
@click.pass_obj
def set_netbox_private_key_file(obj, file):
    obj.netbox_private_key_file = file
    click.echo(
        'netbox-private-key-file set to: {}'.format(
            obj.netbox_private_key_file)
    )


@config_set.command(name='netbox-token')
@click.pass_obj
def set_netbox_token(obj):
    token = click.prompt('Token')
    obj.netbox_token = token
    click.echo('netbox-token set')


@config_set.command(name='arin-parent-org-handle')
@click.argument('value')
@click.pass_obj
def set_arin_parent_org_handle(obj, value):
    obj.arin_parent_org_handle = value
    click.echo(
        'arin-parent-org-handle set to: {}'.format(obj.arin_parent_org_handle)
    )


@config_set.command(name='arin-origin-ases')
@click.argument('value')
@click.pass_obj
def set_arin_origin_ases(obj, value):
    obj.arin_origin_ases = value
    click.echo(
        'arin-origin-ases set to: {}'.format(obj.arin_origin_ases)
    )


@config_set.command(name='arin-api-key')
@click.pass_obj
def set_arin_api_key(obj):
    key = click.prompt('API Key')
    obj.arin_api_key = key
    click.echo('arin-api-key set')


@config_set.command(name='google-api-key')
@click.pass_obj
def set_google_api_key(obj):
    key = click.prompt('API Key')
    obj.google_api_key = key
    click.echo('google-api-key set')


# pylint: disable=no-value-for-parameter,unexpected-keyword-arg
if __name__ == '__main__':
    try:
        cli(auto_envvar_prefix='NETBOX_CLI')
    except pynetbox.core.query.RequestError as e:
        logger.debug(e)

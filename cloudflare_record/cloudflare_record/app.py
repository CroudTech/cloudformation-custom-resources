from crhelper import CfnResource
import CloudFlare
import boto3
import json
import re
import logging
import dns.resolver

class CfnCloudFlare:
    def __init__(self, ssm_prefix="/cfn/custom_resource_config/cloudflare"):
        self.ssm_prefix = ssm_prefix

    def getConfig(self):
        ssm = boto3.client('ssm')
        email = ssm.get_parameter(Name="%s/%s" % (self.ssm_prefix, "email"), WithDecryption=True)["Parameter"]["Value"]
        key = ssm.get_parameter(Name="%s/%s" % (self.ssm_prefix, "key"), WithDecryption=True)["Parameter"]["Value"]
        return {
            "email": email,
            "token": key
        }

    @property
    def Cloudflare(self):
        if not hasattr(self, "_cloudflare"):
            self._cloudflare = CloudFlare.CloudFlare(**self.getConfig())

        return self._cloudflare
    
    @property
    def zone_map(self):
        if not hasattr(self, "_zone_map"):
            self._zone_map = {}
            for zone in self.zones:
                self._zone_map[zone["name"]] = zone["id"]
        return self._zone_map

    @property
    def zones(self):
        if not hasattr(self, "_zones"):
            self._zones = self.Cloudflare.zones.get(params={'per_page':100})
                
        return self._zones

    def updateRecord(self, type, name, value, zone_id, ttl, proxied, record_id):
        result = {
            "action": "updated",
            "record": {}
        }
        dns_record = {
            "name": name,
            "type": type,
            "content": value
        }
        result["record"] = self.Cloudflare.zones.dns_records.put(zone_id, record_id, data=dns_record)

        return result

    def createRecord(self, type, name, value, zone_id, ttl, proxied):
        result = {
            "action": "created",
            "record": {}
        }
        dns_record = {
            "name": name,
            "type": type,
            "content": value
        }
        result["record"] = self.Cloudflare.zones.dns_records.post(zone_id, data=dns_record)

        return result

    def getZone(self, domain):
        try:
            zones = self.Cloudflare.zones.get(params = {'name':domain,'per_page':1})
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones.get %d %s - api call failed' % (e, e))
        except Exception as e:
            exit('/zones.get - %s - api call failed' % (e))

        if len(zones) == 0:
            exit('No zones found')
        
        return zones[0]

    def getZoneId(self, domain):
        return self.getZone(domain)["id"]
    
    def deleteRecord(self, zone_id, record_id):
        self.Cloudflare.zones.dns_records.delete(zone_id, record_id)

    def chechDns(self, domain, type, name, value):
        if not re.search("/%s$/" % re.escape(domain), name):
            name = "%s.%s" % (name, domain)
        resolver = dns.resolver.Resolver()
        try:
            result = resolver.query(qname=name, rdtype=type)
            return result
        except DNSException as e:
            self.output.error(str(e))

logger = logging.getLogger(__name__)
helper = CfnResource()
cf = CfnCloudFlare()

@helper.create
@helper.update
def upsert_record(event, _):
    zone_name = event['ResourceProperties']['ZoneName']
    name = event['ResourceProperties']['Name']
    type = event['ResourceProperties']['Type']
    value = event['ResourceProperties']['Value']
    proxied = event['ResourceProperties']['Proxied']
    ttl = event['ResourceProperties']['TTL']

    zone_id = cf.getZoneId(zone_name)
    if "PhysicalResourceId" in event:
        logger.debug("updating record")
        result = cf.updateRecord(
            type=type,
            name=name,
            value=value,
            zone_id=zone_id,
            ttl=ttl,
            proxied=proxied,
            record_id=event["PhysicalResourceId"]
        )
    else:
        logger.debug("creating record")
        result = cf.createRecord(
            type=type,
            name=name,
            value=value,
            zone_id=zone_id,
            ttl=ttl,
            proxied=proxied
        )
    helper.Data['RecordId'] = result['record']['id']
    helper.Data['ZoneId'] = zone_id
    logger.info(result['record']['id'])
    return result['record']['id']
    
@helper.delete
def delete_record(event, __):
    zone_name = event['ResourceProperties']['ZoneName']
    zone_id = cf.getZoneId(zone_name)

    cf.deleteRecord(
        zone_id=zone_id,
        record_id=event["PhysicalResourceId"]
    )

    return True

# @helper.poll_create
# def poll_create(event, context):
#     if event['ResourceProperties']['Proxied']:
#         return True
#     zone_name = event['ResourceProperties']['ZoneName']
#     name = event['ResourceProperties']['Name']
#     type = event['ResourceProperties']['Type']
#     value = event['ResourceProperties']['Value']

#     return str(cf.chechDns(zone_name, type, name, value)) == value

def handler(event, context):
    helper(event, context)


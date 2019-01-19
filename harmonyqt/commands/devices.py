# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

import math
import platform
from multiprocessing.pool import ThreadPool
from typing import List, Optional

from PyQt5.QtCore import QDateTime

from matrix_client.client import MatrixClient
from matrix_client.crypto.olm_device import OlmDevice
from matrix_client.device import Device

from . import register
from .. import main_window
from ..chat import Chat
from ..utils import get_ip_info

DATE_FORMAT = "yyyy-MM-dd HH:mm:ss"

# TODO: fix verified/etc not saved/loaded for the VM device,
#       message display bug, decrypt error from our own device


@register
def devices(chat: Chat, args: dict) -> None:
    """
    Usage:
      /devices [USER_ID]
      /devices (trust|blacklist|ignore) DEVICE_ID [USER_ID]
      /devices rename DEVICE_ID [NEW_NAME]
      /devices remove DEVICES_ID...
      /devices keep DEVICES_ID...

    Manage user devices.

    If `USER_ID` isn't specified, your current user is assumed.
    If no action is specified, devices for you or `USER_ID` will be listed.

    Actions:
      `trust DEVICE_ID [USER_ID]:`
        Confirm the device truly belongs to its owner,
        allow it to receive encrypted messages you send.

      `blacklist DEVICE_ID [USER_ID]:`
        The device is not trustable,
        prevent it from receiving encrypted messages you send.

      `ignore DEVICE_ID [USER_ID]:`
        The device will receive encrypted messages in any case.

      `rename DEVICE_ID [NEW_NAME]:`
        Set the display name of one of your device.
        If `NEW_NAME` isn't specified,
        it will be reset back to default (`Harmony on <OS> <version>`).

      `remove DEVICES_ID...:`
        Log out and delete one or many devices listed as yours.

      `keep DEVICES_ID...:`
        Like `remove`, but instead deletes all devices except `DEVICES_ID`.

    To verify that another device listed as yours can be trusted:
      - From that device, check its ID and key by e.g.
        typing `/devices` from Harmony or going to User Settings in Riot
      - Ensure that these match with what you see by typing `/devices` here.

    To verify that someone else's device can be trusted:
      - Ask them for the device's ID and key they see, using some other
        mean of communication (e.g. email or phone call)
      - Ensure that these match with what you see by typing `/devices` here.

    Devices that you don't recognize or that fails the check above
    could be attackers eavesdropping.
    They should be blacklisted, or removed if they are listed as yours.

    Examples:
    ```
      /devices
      /devices trust OWNDEVICE1

      /devices @someone:matrix.org
      /devices trust EXAMPLE123 @someone:matrix.org
      /devices blacklist BAD4567890 @someone:matrix.org

      /devices rename OWNDEVICE1 "Harmony on my laptop"
      /devices remove OWNDEVICE2 EXAMPLE456
    ```"""

    acts = (args["trust"], args["blacklist"], args["ignore"], args["remove"])

    user = args["USER_ID"]
    user = chat.client.user_id if not user or user == "@" else user

    if args["rename"]:
        device_rename(client    = chat.client,
                      device_id = args["DEVICE_ID"],
                      new_name  = args["NEW_NAME"])

    elif args["remove"] or args["keep"]:
        raise NotImplementedError("Not implemented, use blacklist for now.")

    elif sum(acts) == 1:
        device_set(chat      = chat,
                   user_id   = user,
                   device_id = args["DEVICE_ID"],
                   trust     = args["trust"],
                   blacklist = args["blacklist"],
                   ignore    = args["ignore"])

    device_list(chat=chat, user_id=user)


def device_list(chat: Chat, user_id: str) -> None:
    chat.logger.info("Retrieving devices info...")
    is_own = user_id in main_window().accounts

    chat.client.olm_device.device_list.get_room_device_keys(chat.room)

    this: List[OlmDevice] = []
    if is_own:
        own_client = main_window().accounts[user_id]
        this       = [own_client.olm_device]
        # Our current device is in this list only if its trust is set
        others     = [d for d in own_client.user.devices.values()
                      if d.device_id != this[0].device_id]
    else:
        others = [
            d for d in
            chat.client.olm_device.device_list.device_keys[user_id].values()
            if not this or d.device_id != this[0].device_id
        ]

    if not this + others:
        chat.logger.error(f"No devices found or unknown user: `{user_id}`.")
        return

    def get_info(device) -> None:
        device.country = None
        if is_own:
            device.get_info()

            if device.device_id == chat.client.device_id and \
               not device.last_seen_ip or device.last_seen_ip == "-":
                info                = get_ip_info()
                device.last_seen_ip = info.get("ip")
                device.country      = info.get("country")

            elif device.last_seen_ip and device.last_seen_ip != "-":
                device.country = get_ip_info(device.last_seen_ip)\
                                 .get("country")

    ThreadPool(8).map(get_info, this + others)
    others.sort(key=lambda d: -d.last_seen_ts if d.last_seen_ts else math.inf)

    fmt_name = lambda n: n or f"<em>Un{'set' if is_own else 'known'}</em>"

    fmt_key  = lambda k: "?" if not k else \
                         " ".join((k[i:i+4] for i in range(0, len(k), 4)))

    fmt_time = lambda t: "" if not t or not isinstance(t, int) else \
                         QDateTime.fromMSecsSinceEpoch(t).toString(DATE_FORMAT)

    fmt_ip = lambda d: f"{d.last_seen_ip} ({d.country})" if d.country else \
                       f"?" if d.last_seen_ip == "-" else \
                       d.last_seen_ip

    span      = lambda t: f"<span class='trust-label-{t.lower()}'>{t}</span>"
    fmt_trust = lambda d: (span("Blacklisted") if d.blacklisted         else
                           span("Verified")    if d.verified            else
                           span("Ignored")     if d.ignored             else
                           span("Undecided"))

    infos = [{
        "Name:":      fmt_name(d.display_name),
        "ID:":        d.device_id or "?",
        "Key:":       fmt_key(d.ed25519),
        "Last IP:":   fmt_ip(d),
        "Last seen:": fmt_time(d.last_seen_ts),
        "Trust:":     fmt_trust(d),
    } for d in this + others]

    max_k = len(max(infos[0].keys(), key=len))
    text  = "\n\n".join((
        ("\n".join((f"{k:{max_k}} {v}" for k, v in i.items() if v)))
        for i in infos
    ))

    if this and this[0].device_id == chat.client.olm_device.device_id:
        dev_texts    = text.split("\n\n")
        dev_texts[0] = f"<strong>{dev_texts[0]}</strong>"
        text         = "\n\n".join(dev_texts)

    chat.logger.info(f"<pre>{text}</pre>", is_html=True)


def device_set(chat:       Chat,
               user_id:    str,
               device_id:  str,
               trust:      bool = False,
               blacklist:  bool = False,
               ignore:     bool = False) -> None:

    assert sum((trust, blacklist, ignore)) == 1, \
           "Expected ONE of trust, blacklist or ignore."

    def _act_on_device(dev: Device) -> None:
        print("act 0", dev.user_id, dev.device_id)
        if blacklist:
            dev.blacklisted = True
            dev.verified    = False
            dev.ignored     = False
        elif trust:
            dev.verified    = True
            dev.blacklisted = False
            dev.ignored     = False
        else:
            dev.ignored     = True
            dev.verified    = False
            dev.blacklisted = False

        save_dict = {dev.user_id: {dev.device_id: dev}}

        for cli in main_window().accounts.values():
            cli.olm_device.db.save_device_keys(save_dict)
            cli.olm_device.db.load_device_keys(cli.api,
                                               cli.olm_device.device_keys)

    for client in main_window().accounts.values():
        if client.device_id == device_id:
            _act_on_device(client.olm_device)
            return

    dev_list = chat.client.olm_device.device_list
    dev_list.get_room_device_keys(chat.room)

    try:
        dev = dev_list.device_keys[user_id][device_id]
    except KeyError:
        chat.logger.error(
            f"User `{user_id}` or device `{device_id}` not found."
        )
        return

    _act_on_device(dev)


def device_rename(client:    MatrixClient,
                  device_id: Optional[str] = None,
                  new_name:  Optional[str] = None) -> None:
    if not str(new_name).strip():
        os_ = f" on {platform.system()}".rstrip()
        os_ = f"{os_} {platform.release()}".rstrip() if os_ != " on" else ""
        new_name = f"Harmony{os_}"

    client.api.update_device_info(device_id or client.device_id, new_name)


def set_default_device_name_if_empty(client: MatrixClient) -> None:
    client.olm_device.get_info()

    if not str(client.olm_device.display_name).strip():
        device_rename(client=client)

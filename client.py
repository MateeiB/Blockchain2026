from ipv8.community import Community, CommunitySettings
from dataclasses import dataclass
from ipv8.messaging.payload_dataclass import DataClassPayload
import asyncio
from pow import mine
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8_service import IPv8
from ipv8.lazy_community import lazy_wrapper


@dataclass
class SubmitPayload(DataClassPayload[1]):
    email: str
    github_url: str
    nonce: int

@dataclass
class ResponsePayload(DataClassPayload[2]):
    success: bool
    message: str

class Lab1Settings(CommunitySettings):
    email: str = ""
    github_url: str = ""

class Lab1Community(Community):
    community_id = bytes.fromhex("2c1cc6e35ff484f99ebdfb6108477783c0102881")
    settings_class = Lab1Settings

    def __init__(self, settings: Lab1Settings):
        super().__init__(settings)
        self.email = settings.email
        self.github_url = settings.github_url
        self.server_pk = bytes.fromhex("4c69624e61434c504b3a86b23934a28d669c390e2d1fc0b0870706c4591cc0cb178bc5a811da6d87d27ef319b2638ef60cc8d119724f4c53a1ebfad919c3ac4136c501ce5c09364e0ebb")
        self.add_message_handler(ResponsePayload, self.on_response)
    
    @lazy_wrapper(ResponsePayload)
    def on_response(self, peer, payload):
        if peer.public_key.key_to_bin() != self.server_pk:
            print("Ignored response from non-server peer")
            return
        print(f"Success: {payload.success}")
        print(f"Message: {payload.message}")

    def send(self, nonce:int):
        for peer in self.get_peers():
            if peer.public_key.key_to_bin() == self.server_pk:
                print("Server found")
                msg1 = SubmitPayload(self.email, self.github_url, nonce)
                self.ez_send(peer, msg1)
                return
        print("No server?")


async def main():
    email = "m.bordea@student.tudelft.nl"
    github_url = "https://github.com/MateeiB/Blockchain2026"
    print("Mining")
    nonce = mine(email, github_url)
    print(f"Found nonce: {nonce}") 
    # start IPv8
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my key", "curve25519", "my_key.pem")
    builder.add_overlay("Lab1Community", "my key", [WalkerDefinition(Strategy.RandomWalk, 50, {"timeout": 1.0})],
    default_bootstrap_defs, {"email": email, "github_url": github_url}, [])
    ipv8 = IPv8(builder.finalize(), extra_communities={"Lab1Community": Lab1Community})
    await ipv8.start()
    community = ipv8.get_overlay(Lab1Community)    
    print("My pubkey:", community.my_peer.public_key.key_to_bin().hex())
    # wait for peer discovery
    print("Waiting for server peer...")
    attempts = 0
    while True:
        found = False
        peers = community.get_peers()
        print(f"  network total: {len(community.network.verified_peers)}")
        if attempts % 5 == 0:
            print(f"  [discovery] {len(peers)} peers in community so far")
            for p in peers:
                print(f"    - {p.public_key.key_to_bin().hex()}...")
        for peer in peers:
            if peer.public_key.key_to_bin() == community.server_pk:
                community.server_peer = peer
                found = True
                break
        if found:
            break
        await asyncio.sleep(1)
        attempts += 1
    # send submission
    community.send(nonce)
    # wait for response
    print("Waiting for response...")
    await asyncio.sleep(5)
    # stop IPv8
    await ipv8.stop()

if __name__ == "__main__":
    asyncio.run(main())


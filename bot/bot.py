import sc2
import random
from sc2 import BotAI, Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.player import Bot, Computer

class CompetitiveBot(BotAI):
	NAME: str = "CompetitiveBot"
	"""This bot's name"""
	RACE: Race = Race.Protoss
	"""This bot's Starcraft 2 race.
	Options are:
		Race.Terran
		Race.Zerg
		Race.Protoss
		Race.Random
	"""

	def __init__(self):
		self.first_attack = False
		self.proxy_built = False
		self.late_game = False

	async def on_start(self):
		print("Game started")
		# Do things here before the game starts

	async def on_step(self, iteration):
		# Populate this function with whatever your bot should do!
		await self.distribute_workers()
		await self.build_workers()
		await self.buidl_pylon()
		await self.build_gateway()
		await self.build_gas()
		await self.build_cyber_core()
		await self.build_four_gates()
		await self.train_stalker()
		await self.chrono()
		await self.warpgate_research()
		await self.attack()
		await self.warp_stalker()
		await self.micro()

		pass

	async def build_workers(self):
		nexus = self.townhalls.ready.random
		if (
			self.can_afford(UnitTypeId.PROBE)
			and nexus.is_idle
			and self.workers.amount < self.townhalls.amount * 22
		):
			nexus.train(UnitTypeId.PROBE)
	
	async def buidl_pylon(self):
		nexus = self.townhalls.ready.random
		pos = nexus.position.towards(self.enemy_start_locations[0], 10)
		
		if (
			self.supply_left < 3
			and self.already_pending(UnitTypeId.PYLON) == 0
			and self.can_afford(UnitTypeId.PYLON)
		):
			await self.build(UnitTypeId.PYLON, near = pos)
		
		#proxy pylon
		if (
			self.structures(UnitTypeId.GATEWAY).amount == 4
			and not self.proxy_built
			and self.can_afford(UnitTypeId.PYLON)
		):
			pos = self.game_info.map_center.towards(self.enemy_start_locations[0], 20)
			await self.build(UnitTypeId.PYLON, near = pos)
			self.proxy_built = True
	
	async def build_gateway(self):
		if (
			self.structures(UnitTypeId.PYLON).ready
			and self.can_afford(UnitTypeId.GATEWAY)
			and not self.structures(UnitTypeId.GATEWAY)
			and self.structures(UnitTypeId.WARPGATE).amount == 0
		):
			pylon = self.structures(UnitTypeId.PYLON).ready.random
			await self.build(UnitTypeId.GATEWAY, near = pylon)

	async def build_gas(self):
		if self.structures(UnitTypeId.GATEWAY):
			for nexus in self.townhalls.ready:
				vgs = self.vespene_geyser.closer_than(15, nexus)
				for vg in vgs:
					if	not self.can_afford(UnitTypeId.ASSIMILATOR):
						break
					worker = self.select_build_worker(vg.position)
					if worker is None:
						break
					if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
						worker.build(UnitTypeId.ASSIMILATOR, vg)
						worker.stop(queue=True)

	async def build_cyber_core(self):
		if self.structures(UnitTypeId.PYLON).ready:
			pylon = self.structures(UnitTypeId.PYLON).ready.random
			if self.structures(UnitTypeId.GATEWAY).ready:
				if not self.structures(UnitTypeId.CYBERNETICSCORE):
					if(
						self.can_afford(UnitTypeId.CYBERNETICSCORE)
						and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0
					):
						await self.build(UnitTypeId.CYBERNETICSCORE, near = pylon)

	async def train_stalker(self):
		for gateway in self.structures(UnitTypeId.GATEWAY).ready:
			if (
				self.can_afford(UnitTypeId.STALKER)
				and gateway.is_idle
			):
				gateway.train(UnitTypeId.STALKER)
	
	async def build_four_gates(self):
		if (
			self.structures(UnitTypeId.PYLON).ready
			and self.can_afford(UnitTypeId.GATEWAY)
			and self.structures(UnitTypeId.GATEWAY).amount + self.structures(UnitTypeId.WARPGATE).amount < 4
		):
			pylon = self.structures(UnitTypeId.PYLON).ready.random
			await self.build(UnitTypeId.GATEWAY, near = pylon)
	
	async def chrono(self):
		if self.structures(UnitTypeId.PYLON):
			nexus = self.townhalls.ready.random
			if(
				not self.structures(UnitTypeId.CYBERNETICSCORE).ready
				and self.structures(UnitTypeId.PYLON).amount > 0
			):
				if nexus.energy >= 50:
					nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
			else:
				if nexus.energy >= 50:
					cybercore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.random
					nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, cybercore)

	
	async def warpgate_research(self):
		if (
			self.structures(UnitTypeId.CYBERNETICSCORE).ready
			and self.can_afford(AbilityId.RESEARCH_WARPGATE)
			and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0
		):
			cybercore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
			cybercore.research(UpgradeId.WARPGATERESEARCH)
	
	async def attack(self):
		stalkercount = self.units(UnitTypeId.STALKER).amount
		stalkers = self.units(UnitTypeId.STALKER).ready.idle
		target = self.structures.random_or(self.enemy_start_locations[0]).position
		
		if self. structures(UnitTypeId.PYLON).ready:
			proxy = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0])
			proxyposition = proxy.position.random_on_distance(3)

		for stalker in stalkers:
			if stalkercount >= 8:
				targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
				if targets:
					target = targets.closest_to(stalker)
					stalker.attack(target)
				else:
					stalker.attack(self.enemy_start_locations[0])
			else:
				stalker.attack(proxyposition)

	async def warp_stalker(self):
		for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
			abilities = await self.get_available_abilities(warpgate)
			proxy = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0])
			if AbilityId.WARPGATETRAIN_STALKER in abilities and self.can_afford(UnitTypeId.STALKER):
				placement = proxy.position.random_on_distance(3)
				warpgate.warp_in(UnitTypeId.STALKER, placement)
	
	async def micro(self):
		stalkers = self.units(UnitTypeId.STALKER)
		enemy_location = self.enemy_start_locations[0]

		if self.structures(UnitTypeId.PYLON).ready and self.first_attack:
			pylon = self.structures(UnitTypeId.PYLON).closest_to(enemy_location)
			for stalker in stalkers:
				if stalker.weapon_cooldown == 0:
					stalker.attack(enemy_location)
				elif stalker.weapon_cooldown < 0:
					stalker.move(pylon)
				else:
					stalker.move(pylon)

	def on_end(self, result):
		print("Game ended.")
		# Do things here after the game ends

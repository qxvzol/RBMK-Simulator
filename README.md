"Simple" RBMK Nuclear reactor simulator. Current features include neutron behaviour. Do not expect this to be updated often.

## Features/Planning:
### In-tile phyics
#### Neutron Physics: WIP
- Simulation of fast and thermal neutrons, absorption, moderation, fission, etc.
- Done using coupled matrix calculations do achieve smaller timestep
- Affects from various other factors, e.g. Doppler effect at different temp. and steam void formation
- Xenon production and poisoning
- **Testing**: Checking neutron behaviour when left on own, checking reactivity, checking how changing factors affect behaviour
#### Steam formation: Incomplete
- Dependent on pressure and temperature of water
- Absorbs excess energy to boil based on specific latent heat
- Forms steam which increases pressure, decreases neutron absorption
- Regulated by steam drums (steam output to turbines)
- **Testing**: Checking if steam formation accurate at varying temperatures and energy outputs, as well as steam effects on pressure an neutron behaviour
#### Heat transfer: WIP
- Heat simulated as energy rather than temp; temp calculated based on current energy every tick
- Between materials within tile.
- mostly generated in fuel, some heat generated elswhere via neutron/EM radiation interaction
- Also includes transfer of steam upwards
- **Testing**: by setting material temp. artificially and checking heat transfer to surrounding materials
### Inter-tile physics:
#### Heat transfer: Incomplete
- Heat also simulated as energy, as in heat simulation within tiles
- Between tiles dependent on material
- large amount of heat transfer done my water convection from pumps
- **Testing**: by setting tile temp. artificially and checking heat transfer to surrounding tiles
#### Neutron diffusion: Incomplete
- Between tiles dependent on neutron density difference
- **Testing**: by setting neutron densities artificially and checking neutron diffusion
### Other features:
#### Warp: WIP
- Accelerates all processes in reactor without affecting simulation tick length
- Allows for "faster reactor" without increasing simulation cost
- **Testing**: Ensuring all processes run as expected when timewarping
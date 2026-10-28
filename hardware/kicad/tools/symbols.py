"""symbols.py - every symbol used by the Flow Bench V2 schematics.

Library symbols are converted from the KiCad 5 library (KiCad's own pinouts).
Custom symbols are drawn from the datasheet pinouts noted beside each one.
"""
from kicadgen import V5Lib, rect_symbol

FP = {
    'R': 'Resistor_SMD:R_0805_2012Metric',
    'C': 'Capacitor_SMD:C_0805_2012Metric',
    'C1206': 'Capacitor_SMD:C_1206_3216Metric',
    'C1210': 'Capacitor_SMD:C_1210_3225Metric',
    'CTANT': 'Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B',
    'CELEC': 'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm',
    'PTC1812': 'Fuse:Fuse_1812_4532Metric',
    'PTC1206': 'Fuse:Fuse_1206_3216Metric',
    'SOT23': 'Package_TO_SOT_SMD:SOT-23',
    'DPAK': 'Package_TO_SOT_SMD:TO-252-2',
    'SMC': 'Diode_SMD:D_SMC',
    'TP': 'TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm',
    'JP2B': 'Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm',
    'JP2O': 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
    'JP3B': 'Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm',
}


def socket(n):
    return 'Connector_PinSocket_2.54mm:PinSocket_1x%02d_P2.54mm_Vertical' % n


def header(n):
    return 'Connector_PinHeader_2.54mm:PinHeader_1x%02d_P2.54mm_Vertical' % n


def mc(n):
    """Phoenix MC 1,5 pluggable terminal block header, 3.81 mm."""
    return 'Connector_Phoenix_MC:PhoenixContact_MC_1,5_%d-G-3.81_1x%02d_P3.81mm_Horizontal' % (n, n)


def mstb(n):
    """Phoenix MSTBA 2,5 pluggable terminal block header, 5.08 mm (power)."""
    return 'Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_%d-G-5,08_1x%02d_P5.08mm_Horizontal' % (n, n)


def load(project, libdir):
    lib = V5Lib(libdir)
    for fn in ['Device.lib', 'Diode.lib', 'Connector.lib', 'Connector_Generic.lib', 'Jumper.lib', 'power.lib',
               'Transistor_BJT.lib', 'Transistor_FET.lib', 'Interface_Expansion.lib', 'Isolator.lib',
               'Transistor_Array.lib', 'Amplifier_Operational.lib', '74xx.lib', 'Regulator_Linear.lib',
               'MCU_Microchip_ATtiny.lib', 'Power_Management.lib']:
        lib.load(fn)
    S = {}

    def conv(defname, name=None, fp=None):
        S[name or defname] = project.sym(lib.symbol(defname, name, fp))

    for n in ['R', 'C', 'C_Polarized', 'Polyfuse', 'D_TVS', 'BAV99', 'TestPoint', 'PWR_FLAG',
              'SolderJumper_2_Bridged', 'SolderJumper_2_Open', 'SolderJumper_3_Bridged12',
              'Q_NPN_BEC', 'Q_NMOS_GSD', 'Q_NMOS_GDS', 'Q_PMOS_GDS', 'Micro_SD_Card_Det']:
        conv(n)
    for k in (2, 3, 4, 5, 6, 7, 8, 10, 12):
        conv('Conn_01x%02d' % k)
    conv('TCA9535PWR', fp='Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm')
    conv('TCA9548APWR', fp='Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm')
    conv('TLP291-4', fp='Package_SO:SOIC-16_4.55x10.3mm_P1.27mm')
    conv('ULN2803A', 'TBD62083AFWG', fp='Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm')     # same pinout
    conv('LM2904', 'MCP6002-xSN', fp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
    conv('74LS123', '74HCT123', fp='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm')
    conv('74HC14', '74LVC14', fp='Package_SO:SOIC-14_3.9x8.7mm_P1.27mm')               # same pinout
    conv('LM1117-3.3', fp='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    conv('ATtiny1616-S', fp='Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm')
    conv('TPS26631PWP')

    # ---- custom symbols (datasheet pinouts)
    S['ADS1219'] = project.sym(rect_symbol(   # TI ADS1219 datasheet, PW (TSSOP-16)
        'ADS1219', 'U',
        left=[('11', 'AIN0', 'input'), ('10', 'AIN1', 'input'), ('7', 'AIN2', 'input'), ('6', 'AIN3', 'input'),
              None, ('9', 'REFP', 'input'), ('8', 'REFN', 'input'), None, ('1', 'A0', 'input'), ('2', 'A1', 'input')],
        right=[('15', 'SDA', 'bidirectional'), ('16', 'SCL', 'input'), None, ('14', '~{DRDY}', 'open_collector'),
               ('3', '~{RESET}', 'input')],
        top=[('12', 'AVDD', 'power_in'), ('13', 'DVDD', 'power_in')],
        bottom=[('5', 'AGND', 'power_in'), ('4', 'DGND', 'power_in')],
        footprint='Package_SO:TSSOP-16_4.4x5mm_P0.65mm', datasheet='https://www.ti.com/lit/ds/symlink/ads1219.pdf',
        description='24-bit 4-channel I2C ADC'))
    S['AM26C31'] = project.sym(rect_symbol(   # TI AM26C31 datasheet, D (SOIC-16)
        'AM26C31', 'U',
        left=[('1', '1A', 'input'), ('7', '2A', 'input'), ('9', '3A', 'input'), ('15', '4A', 'input'), None,
              ('4', 'G', 'input'), ('12', '~{G}', 'input')],
        right=[('2', '1Y', 'output'), ('3', '1Z', 'output'), ('6', '2Y', 'output'), ('5', '2Z', 'output'),
               ('10', '3Y', 'output'), ('11', '3Z', 'output'), ('14', '4Y', 'output'), ('13', '4Z', 'output')],
        top=[('16', 'VCC', 'power_in')], bottom=[('8', 'GND', 'power_in')],
        footprint='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm', datasheet='https://www.ti.com/lit/ds/symlink/am26c31.pdf',
        description='Quad differential line driver'))
    S['TPS7A4901'] = project.sym(rect_symbol(  # TI TPS7A49 datasheet, DGN (HVSSOP-8 PowerPAD)
        'TPS7A4901', 'U',
        left=[('8', 'IN', 'power_in'), ('5', 'EN', 'input'), ('6', 'NR/SS', 'passive'), None,
              ('3', 'NC', 'no_connect'), ('7', 'DNC', 'no_connect')],
        right=[('1', 'OUT', 'power_out'), ('2', 'FB', 'input')],
        bottom=[('4', 'GND', 'power_in'), ('9', 'PAD', 'passive')],
        footprint='Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm_ThermalVias',
        datasheet='https://www.ti.com/lit/ds/symlink/tps7a49.pdf', description='36 V low-noise LDO, adjustable'))
    S['ABP2_I2C'] = project.sym(rect_symbol(   # Honeywell ABP2 datasheet: DIP, I2C output
        'ABP2_I2C', 'U',
        left=[('6', 'NC', 'no_connect'), ('3', 'EOC', 'output')],
        right=[('4', 'SDA', 'bidirectional'), ('2', 'SCL', 'input')],
        top=[('1', 'VDD', 'power_in')], bottom=[('5', 'GND', 'power_in')],
        footprint='', description='Honeywell ABP2 pressure sensor, I2C, DIP. VERIFY PINOUT before layout'))
    S['Pololu_D24V22Fx'] = project.sym(rect_symbol(
        'Pololu_D24V22Fx', 'PS',
        left=[('3', 'VIN', 'power_in'), ('2', 'EN', 'input')],
        right=[('5', 'VOUT', 'power_out'), ('1', 'PG', 'open_collector')],
        bottom=[('4', 'GND', 'power_in'), ('6', 'GND', 'power_in')],
        footprint='FlowBench:Pololu_D24V22Fx',
        datasheet='https://www.pololu.com/product/2858',
        description='Pololu D24V22Fx step-down module: pins 1-5 PG, EN, VIN, GND, VOUT; pin 6 corner GND'))
    devkit_j1 = ['3V3', '3V3', 'RST', 'GPIO4', 'GPIO5', 'GPIO6', 'GPIO7', 'GPIO15', 'GPIO16', 'GPIO17', 'GPIO18',
                 'GPIO8', 'GPIO3', 'GPIO46', 'GPIO9', 'GPIO10', 'GPIO11', 'GPIO12', 'GPIO13', 'GPIO14', '5V', 'GND']
    devkit_j3 = ['GND', 'TX/GPIO43', 'RX/GPIO44', 'GPIO1', 'GPIO2', 'GPIO42', 'GPIO41', 'GPIO40', 'GPIO39',
                 'GPIO38', 'GPIO37', 'GPIO36', 'GPIO35', 'GPIO0', 'GPIO45', 'GPIO48', 'GPIO47', 'GPIO21', 'GPIO20',
                 'GPIO19', 'GND', 'GND']
    S['DevKitC-1_J1'] = project.sym(rect_symbol(
        'DevKitC-1_J1', 'J', right=[(str(i + 1), n) for i, n in enumerate(devkit_j1)], footprint=socket(22),
        description='ESP32-S3-DevKitC-1 header J1 (socket on the board)'))
    S['DevKitC-1_J3'] = project.sym(rect_symbol(
        'DevKitC-1_J3', 'J', left=[(str(i + 1), n) for i, n in enumerate(devkit_j3)], footprint=socket(22),
        description='ESP32-S3-DevKitC-1 header J3 (socket on the board)'))
    S['WIZ850io'] = project.sym(rect_symbol(   # WIZnet WIZ850io: J1 = pads 1-6, J2 = pads 7-12
        'WIZ850io', 'U',
        left=[('1', 'J1-1 GND', 'power_in'), ('2', 'J1-2 GND', 'power_in'), ('3', 'J1-3 MOSI', 'input'),
              ('4', 'J1-4 SCLK', 'input'), ('5', 'J1-5 SCNn', 'input'), ('6', 'J1-6 INTn', 'open_collector')],
        right=[('7', 'J2-1 GND', 'power_in'), ('8', 'J2-2 3V3D', 'power_in'), ('9', 'J2-3 3V3D', 'power_in'),
               ('10', 'J2-4 NC', 'no_connect'), ('11', 'J2-5 RSTn', 'input'), ('12', 'J2-6 MISO', 'output')],
        footprint='FlowBench:WIZ850io',
        description='WIZnet WIZ850io W5500 Ethernet module on two 1x6 sockets, 17.78 mm apart'))
    return S

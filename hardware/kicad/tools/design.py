"""design.py - DIY Flow Bench V2 rev A schematics, as data.

Run:  python3 design.py <path to KiCad 5 symbol library checkout> <output dir>

Writes two KiCad projects:
  flowbench-main/          the main board (plugs in the DevKit, WIZ850io and power module)
  flowbench-power-module/  PM1, the plug-in input power module

Net names follow docs/V2/pin-map.md. Every connection is a named net; the generator
checks that no net has only one connection and that every pin is either on a net or
marked not connected.
"""
import os, sys
from kicadgen import Project, Sheet, Part
import symbols
from symbols import FP, socket, header, mc, mstb

DATE = '2026-10-28'


class Builder:
    def __init__(self, project, S):
        self.p, self.S = project, S
        self.sheet = None

    def on(self, sheet):
        self.sheet = sheet
        return self

    def part(self, prefix, sym, value, nets, **kw):
        return self.sheet.add(Part(self.p.ref(prefix), self.S[sym], value, nets, **kw))

    def R(self, value, a, b, fp=FP['R']):
        return self.part('R', 'R', value, {1: a, 2: b}, footprint=fp)

    def C(self, value, a, b='GND', fp=FP['C']):
        return self.part('C', 'C', value, {1: a, 2: b}, footprint=fp)

    def CP(self, value, plus, minus='GND', fp=FP['CTANT']):
        return self.part('C', 'C_Polarized', value, {1: plus, 2: minus}, footprint=fp)

    def F(self, value, a, b, fp=FP['PTC1812']):
        return self.part('F', 'Polyfuse', value, {1: a, 2: b}, footprint=fp)

    def NPN(self, b, c, e='GND', value='MMBT3904'):
        return self.part('Q', 'Q_NPN_BEC', value, {1: b, 2: e, 3: c}, footprint=FP['SOT23'])

    def TP(self, net):
        return self.part('TP', 'TestPoint', net, {1: net}, footprint=FP['TP'])

    def FLAG(self, net):
        return self.part('#FLG', 'PWR_FLAG', 'PWR_FLAG', {1: net}, footprint='')

    def CONN(self, n, value, nets, fp):
        return self.part('J', 'Conn_01x%02d' % n, value,
                         {i + 1: v for i, v in enumerate(nets)}, footprint=fp)

    def BAV99(self, node, low='GND', high='+5VA'):
        # SOT-23 BAV99: pin 1 anode (to low rail), pin 2 cathode (to high rail), pin 3 common (signal)
        return self.part('D', 'BAV99', 'BAV99', {1: low, 2: high, 3: node}, footprint=FP['SOT23'])

    def high_side(self, enable, out, label):
        """P-MOSFET high-side 24 V switch, gate driven by an NPN; Vgs held near 12 V."""
        g, k = out + '_G', out + '_K'
        self.part('Q', 'Q_PMOS_GDS', 'SUD50P06-15 (60 V P-ch, DPAK)', {1: g, 2: out, 3: '+24V'},
                  footprint=FP['DPAK'], fields={'Function': label})
        self.R('10k', '+24V', g)         # gate to source: off by default
        self.R('10k', g, k)              # gate divider: Vgs about 12 V when on
        self.NPN(enable + '_B', k)
        self.R('10k', enable, enable + '_B')
        self.R('100k', enable + '_B', 'GND')


# =============================================================================== main board

def main_board(libdir):
    p = Project('flowbench-main', 'DIY Flow Bench V2 main board, rev A', date=DATE)
    S = symbols.load(p, libdir)
    b = Builder(p, S)

    pw = Sheet('Power', 'power.kicad_sch', 'Power: input, module sockets, regulators, switched 24 V')
    mcu = Sheet('Controller', 'controller.kicad_sch', 'Controller: ESP32-S3-DevKitC-1-N32R8V sockets')
    net = Sheet('Network and storage', 'network.kicad_sch', 'Ethernet (WIZ850io) and microSD')
    adc = Sheet('Sensors and ADC', 'sensors.kicad_sch', 'I2C, multiplexer, pressure sensors, ADCs')
    fld = Sheet('Field inputs', 'field.kicad_sch', 'MAF, swirl, switches, current sensors, Digimatic')
    io = Sheet('IO and safety', 'io.kicad_sch', 'I/O expanders, optocouplers, steppers, coils, watchdog')
    p.sheets = [pw, mcu, net, adc, fld, io]

    # ------------------------------------------------------------------ power
    b.on(pw)
    pw.note('24 V arrives from the panel XT90 and 7 A breaker on J1. The plug-in power module (PM1) carries the TPS2663 eFuse and the TPS7A4901.')
    pw.note('PM1 returns protected +24V, and makes +5VA (analog 5 V) from +12V. Its eFuse fault and current-monitor outputs go to the expander and ADC #2.')
    pw.note('Pololu D24V22Fx pinout confirmed from the board: PG, EN, VIN, GND, VOUT (1-5) plus a corner GND (6). EN and PG unused.')
    b.CONN(2, '24V IN', ['+24V_RAW', 'GND'], mstb(2))
    b.CONN(12, 'PM1 power socket', ['+24V_RAW'] * 4 + ['GND'] * 4 + ['+24V'] * 4, socket(12))
    b.CONN(6, 'PM1 signal socket', ['+12V', '+5VA', 'GND', 'EFUSE_FLT_N', 'EFUSE_IMON', 'GND'], socket(6))
    b.part('PS', 'Pololu_D24V22Fx', 'D24V22F5 (5 V 2.5 A)', {3: '+24V', 2: None, 5: '+5V', 1: None, 4: 'GND', 6: 'GND'})
    b.part('PS', 'Pololu_D24V22Fx', 'D24V22F12 (12 V 2.2 A)', {3: '+24V', 2: None, 5: '+12V', 1: None, 4: 'GND', 6: 'GND'})
    b.CP('22uF 35V', '+24V', fp=FP['CELEC'])
    b.C('10uF', '+5V', fp=FP['C1206'])
    b.C('10uF', '+12V', fp=FP['C1206'])
    b.part('U', 'LM1117-3.3', 'LM1117-3.3', {1: 'GND', 2: '+3V3', 3: '+5V'})
    b.CP('10uF tant', '+5V')
    b.CP('10uF tant', '+3V3')
    pw.note('LM1117: tantalum (or ESR-specified) 10 uF on input and output, per the TI datasheet.')
    b.high_side('BLEED_PWR_EN', 'BLEED_24V', 'Bleed stepper 24 V (fault reset by power cycle)')
    b.F('PTC 2.5 A hold', 'BLEED_24V', 'BLEED_24V_F')
    b.high_side('LIFT_PWR_EN', 'LIFT_24V', 'Lift stepper 24 V')
    b.F('PTC 2.5 A hold', 'LIFT_24V', 'LIFT_24V_F')
    b.high_side('WD_OK', 'COIL_24V', 'Contactor coil supply, cut by the heartbeat watchdog')
    b.F('PTC 0.1 A hold', '+24V', '+24V_FIELD', fp=FP['PTC1206'])
    pw.note('+24V_FIELD feeds limit switches, the orifice selector and the E-stop status contact, through a 0.1 A PTC.')
    # PWR_FLAG only where no regulator output already drives the net (+5V, +12V, +3V3 have one)
    for n in ['+24V_RAW', '+24V', '+5VA', 'GND']:
        b.FLAG(n)
    for n in ['+24V', '+12V', '+5V', '+3V3', '+5VA', 'GND']:
        b.TP(n)

    # ------------------------------------------------------------------ controller
    b.on(mcu)
    mcu.note('The DevKit plugs into two 22-pin sockets. Its own 3V3 pins are left open: the board makes +3V3 separately.')
    mcu.note('GPIO35-37 are used by the octal flash and PSRAM. GPIO47/48 are 1.8 V on the WROOM-2 and stay unused.')
    j1 = {1: None, 2: None, 3: 'ESP_RST', 4: 'CT3', 5: 'CT4', 6: 'CT5', 7: 'CT6', 8: 'SDA', 9: 'SCL',
          10: 'BLEED_STEP', 11: 'BLEED_DIR', 12: 'MAF_FREQ', 13: 'SD_DAT0_MCU', 14: 'HEARTBEAT', 15: 'SWIRL_A',
          16: 'SWIRL_B', 17: 'SPI_MOSI', 18: 'SPI_SCK', 19: 'SPI_MISO', 20: 'ETH_CS', 21: '+5V', 22: 'GND'}
    j3 = {1: 'GND', 2: 'ESP_TX', 3: 'ESP_RX', 4: 'CT1', 5: 'CT2', 6: 'EXP_INT_N', 7: 'SD_CLK_MCU',
          8: 'LIFT_DIR', 9: 'LIFT_STEP', 10: None, 11: None, 12: None, 13: None, 14: None, 15: None, 16: None,
          17: None, 18: 'SD_CMD', 19: None, 20: None, 21: 'GND', 22: 'GND'}
    b.part('J', 'DevKitC-1_J1', 'ESP32-S3-DevKitC-1 J1', j1)
    b.part('J', 'DevKitC-1_J3', 'ESP32-S3-DevKitC-1 J3', j3)
    b.R('10k', 'HEARTBEAT', 'GND')     # GPIO46 strapping: held low at boot
    b.R('10k', 'BLEED_STEP', 'GND')
    b.R('10k', 'LIFT_STEP', 'GND')
    for n in ['ESP_RST', 'ESP_TX', 'ESP_RX', 'SDA', 'SCL', 'HEARTBEAT']:
        b.TP(n)

    # ------------------------------------------------------------------ network and storage
    b.on(net)
    net.note('WIZ850io: one footprint with both 1x6 sockets (J1 = pads 1-6, J2 = pads 7-12), rows 17.78 mm (0.7 in) apart.')
    net.note('The W5500 is polled (no interrupt). JP3 routes INTn to expander 2 P06 if polling is not enough.')
    net.note('microSD on the ESP32-S3 SD host, 1-bit mode. JP1 can disconnect DAT0 from GPIO3 (a strapping pin) if it upsets boot.')
    b.part('U', 'WIZ850io', 'WIZ850io', {1: 'GND', 2: 'GND', 3: 'SPI_MOSI', 4: 'SPI_SCK', 5: 'ETH_CS', 6: 'ETH_INT_N',
           7: 'GND', 8: '+3V3', 9: '+3V3', 10: None, 11: 'ETH_RST_N', 12: 'SPI_MISO'})
    b.R('10k', '+3V3', 'ETH_CS')
    b.R('10k', '+3V3', 'ETH_INT_N')
    b.R('10k', '+3V3', 'ETH_RST_N')
    b.part('JP', 'SolderJumper_2_Open', 'JP3 ETH INT', {1: 'ETH_INT_N', 2: 'ETH_INT_EXP'}, footprint=FP['JP2O'])
    b.C('10uF', '+3V3', fp=FP['C1206'])
    b.C('100nF', '+3V3')
    b.part('J', 'Micro_SD_Card_Det', 'microSD push-push', {1: 'SD_DAT2', 2: 'SD_DAT3', 3: 'SD_CMD', 4: '+3V3',
           5: 'SD_CLK', 6: 'GND', 7: 'SD_DAT0', 8: 'SD_DAT1', 9: 'GND', 10: 'SD_CD_N', 11: 'GND'},
           footprint='Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5')
    for n in ['SD_CMD', 'SD_DAT0', 'SD_DAT1', 'SD_DAT2', 'SD_DAT3', 'SD_CD_N']:
        b.R('10k', '+3V3', n)
    b.R('33R', 'SD_CLK_MCU', 'SD_CLK')
    b.part('JP', 'SolderJumper_2_Bridged', 'JP1 SD DAT0', {1: 'SD_DAT0_MCU', 2: 'SD_DAT0'}, footprint=FP['JP2B'])
    b.C('10uF', '+3V3', fp=FP['C1206'])
    b.C('100nF', '+3V3')
    for n in ['SPI_SCK', 'SD_CLK', 'SD_CMD', 'SD_DAT0']:
        b.TP(n)

    # ------------------------------------------------------------------ sensors and ADC
    b.on(adc)
    adc.note('Main I2C bus: expanders 0x20/0x21, Digimatic ATtiny 0x30, ADS1219 #1 0x40, ADS1219 #2 0x41, TCA9548A 0x70.')
    adc.note('ADS1219 #2 moved from mux channel 4 to the main bus at 0x41: at 0x40 behind the mux it would clash with ADS1219 #1.')
    adc.note('Behind the mux: ABP2 reference ch0, orifice ch1, pitot ch2 (all 0x28), BME280 cable ch3 (0x77). Ch4-7 spare.')
    b.R('2.2k', '+3V3', 'SDA')
    b.R('2.2k', '+3V3', 'SCL')
    mux = {1: 'GND', 2: 'GND', 21: 'GND', 3: 'MUX_RST_N', 22: 'SCL', 23: 'SDA', 24: '+3V3', 12: 'GND'}
    for ch in range(8):
        sd, sc = 4 + 2 * ch + (1 if ch >= 4 else 0), 5 + 2 * ch + (1 if ch >= 4 else 0)
        mux[sd] = 'MUX%d_SDA' % ch if ch < 4 else None
        mux[sc] = 'MUX%d_SCL' % ch if ch < 4 else None
    b.part('U', 'TCA9548APWR', 'TCA9548APWR', mux)
    b.R('10k', '+3V3', 'MUX_RST_N')
    b.C('100nF', '+3V3')
    for ch in range(4):
        b.R('4.7k', '+3V3', 'MUX%d_SDA' % ch)
        b.R('4.7k', '+3V3', 'MUX%d_SCL' % ch)
    for ch, name in enumerate(['Reference', 'Orifice', 'Pitot']):
        b.part('U', 'ABP2_I2C', 'ABP2DRRN100MD2A3XX', {1: '+3V3', 2: 'MUX%d_SCL' % ch, 3: None, 4: 'MUX%d_SDA' % ch,
               5: 'GND', 6: None}, fields={'Function': name + ' pressure'})
        b.C('100nF', '+3V3')
    b.CONN(4, 'BME280 (GX12-4)', ['+3V3', 'GND', 'MUX3_SDA', 'MUX3_SCL'], mc(4))
    b.part('U', 'ADS1219', 'ADS1219 #1 (0x40)', {11: 'MAF_SIG_ADC', 10: 'MAF_IAT_ADC', 7: 'MON_5VA', 6: 'MON_24V',
           9: '+5VA', 8: 'GND', 1: 'GND', 2: 'GND', 15: 'SDA', 16: 'SCL', 14: None, 3: 'ADC_RST_N',
           12: '+5VA', 13: '+3V3', 5: 'GND', 4: 'GND'})
    b.part('U', 'ADS1219', 'ADS1219 #2 (0x41)', {11: 'EFUSE_IMON', 10: 'MAF_ID_ADC', 7: 'ADC2_AIN2', 6: 'ADC2_AIN3',
           9: '+5VA', 8: 'GND', 1: '+3V3', 2: 'GND', 15: 'SDA', 16: 'SCL', 14: None, 3: 'ADC_RST_N',
           12: '+5VA', 13: '+3V3', 5: 'GND', 4: 'GND'})
    b.R('10k', '+3V3', 'ADC_RST_N')
    for n in ['+5VA', '+3V3', '+5VA', '+3V3']:
        b.C('100nF', n)
    b.C('1uF', '+5VA')
    b.R('150k', '+24V', 'MON_24V')     # 1/16 divider
    b.R('10k', 'MON_24V', 'GND')
    b.C('100nF', 'MON_24V')
    b.R('30k', '+5VA', 'MON_5VA')      # 1/4 divider
    b.R('10k', 'MON_5VA', 'GND')
    b.C('100nF', 'MON_5VA')
    b.C('10nF', 'EFUSE_IMON')
    b.TP('ADC2_AIN2')
    b.TP('ADC2_AIN3')

    # ------------------------------------------------------------------ field inputs
    b.on(fld)
    fld.note('MAF connector (GX12-7): separate analog and frequency pins; the harness uses the one that matches the MAF.')
    fld.note('Bosch 0280218335 is analog 0-5 V, harness ID 1.0 k. JP2 adds a 5 V pull-up for open-collector frequency MAFs.')
    b.CONN(7, 'MAF (GX12-7)', ['MAF_12V', 'GND', 'MAF_SIG', 'MAF_FREQ_IN', 'MAF_IAT', 'MAF_5VREF', 'MAF_ID'], mc(7))
    b.F('PTC 0.5 A hold', '+12V', 'MAF_12V', fp=FP['PTC1206'])
    b.R('100R', '+5VA', 'MAF_5VREF')
    b.R('1k', 'MAF_SIG', 'MAF_SIG_P')
    b.BAV99('MAF_SIG_P')
    b.R('15k', 'MAF_SIG_P', 'MAF_SIG_ADC')
    b.R('10k', 'MAF_SIG_ADC', 'GND')
    b.C('10nF', 'MAF_SIG_ADC')
    b.R('2.49k', '+5VA', 'MAF_IAT')
    b.R('1k', 'MAF_IAT', 'MAF_IAT_ADC')
    b.BAV99('MAF_IAT_ADC')
    b.C('100nF', 'MAF_IAT_ADC')
    b.R('10k', '+5VA', 'MAF_ID')
    b.R('1k', 'MAF_ID', 'MAF_ID_ADC')
    b.BAV99('MAF_ID_ADC')
    b.C('100nF', 'MAF_ID_ADC')
    b.part('JP', 'SolderJumper_2_Open', 'JP2 MAF freq pull-up', {1: 'MAF_FREQ_IN', 2: 'MAF_FREQ_PU'}, footprint=FP['JP2O'])
    b.R('4.7k', 'MAF_FREQ_PU', '+5V')
    b.R('1k', 'MAF_FREQ_IN', 'MAF_FREQ_P')
    b.R('10k', 'MAF_FREQ_P', 'GND')
    b.CONN(5, 'Swirl encoder (GX12-5)', ['+5V', 'GND', 'SWIRL_A_IN', 'SWIRL_B_IN', None], mc(5))
    for ch in ['A', 'B']:
        b.R('4.7k', '+5V', 'SWIRL_%s_IN' % ch)
        b.R('1k', 'SWIRL_%s_IN' % ch, 'SWIRL_%s_P' % ch)
    b.part('U', '74LVC14', '74LVC14 (5 V-tolerant inputs)', {1: 'MAF_FREQ_P', 2: 'MAF_FREQ', 3: 'SWIRL_A_P', 4: 'SWIRL_A',
           5: 'SWIRL_B_P', 6: 'SWIRL_B', 9: 'GND', 8: None, 11: 'GND', 10: None, 13: 'GND', 12: None,
           14: '+3V3', 7: 'GND'})
    b.C('100nF', '+3V3')
    b.CONN(3, 'Bleed home switch (GX12-3)', ['+24V_FIELD', 'BLEED_HOME_IN', 'GND'], mc(3))
    b.CONN(4, 'Lift switches (GX12-4)', ['+24V_FIELD', 'LIFT_HOME_IN', 'LIFT_MAX_IN', 'GND'], mc(4))
    b.CONN(5, 'Orifice selector (GX12-5)', ['+24V_FIELD', 'ORIF_B0_IN', 'ORIF_B1_IN', 'ORIF_B2_IN', 'GND'], mc(5))
    # current transformers
    fld.note('Current transformers (SCT-013-010, 1 V at 10 A) share a 1.65 V bias; each is read on an ADC1 GPIO.')
    b.CONN(8, 'Motor current sensors (GX16-8)', ['CT%d_IN' % i for i in range(1, 7)] + ['CT_BIAS', 'GND'], mc(8))
    b.R('10k', '+3V3', 'CT_BIAS_DIV')
    b.R('10k', 'CT_BIAS_DIV', 'GND')
    b.C('100nF', 'CT_BIAS_DIV')
    b.part('U', 'MCP6002-xSN', 'MCP6002', {3: 'CT_BIAS_DIV', 2: 'CT_BIAS', 1: 'CT_BIAS', 5: 'GND', 6: 'OPB_FB',
           7: 'OPB_FB', 8: '+3V3', 4: 'GND'})
    b.C('10uF', 'CT_BIAS', fp=FP['C1206'])
    b.C('100nF', '+3V3')
    for i in range(1, 7):
        b.R('1k', 'CT%d_IN' % i, 'CT%d' % i)
        b.C('10nF', 'CT%d' % i)
    # Digimatic interface
    fld.note('Digimatic: ATtiny1616 runs firmware/digimatic-interface. JP4/JP5 pick direct (1-2, default) or the NPN inverter (2-3, fit Q).')
    b.CONN(4, 'Digimatic indicator (GX12-4)', ['GND', 'DIGI_DATA', 'DIGI_CLK', 'DIGI_REQ'], mc(4))
    for sig in ['CLK', 'DATA']:
        b.R('10k', '+3V3', 'DIGI_%s' % sig)
        b.part('JP', 'SolderJumper_3_Bridged12', 'JP %s direct/inverted' % sig,
               {1: 'DIGI_%s' % sig, 2: 'DIGI_%s_MCU' % sig, 3: 'DIGI_%s_INV' % sig}, footprint=FP['JP3B'])
        b.R('10k', 'DIGI_%s' % sig, 'DIGI_%s_QB' % sig)
        q = b.NPN('DIGI_%s_QB' % sig, 'DIGI_%s_INV' % sig)
        q.dnp = True
        b.R('10k', '+3V3', 'DIGI_%s_INV' % sig)
    b.NPN('DIGI_REQ_B', 'DIGI_REQ')
    b.R('10k', 'DIGI_REQ_DRV', 'DIGI_REQ_B')
    b.R('100k', 'DIGI_REQ_B', 'GND')
    b.part('U', 'ATtiny1616-S', 'ATtiny1616-SN', {1: '+3V3', 20: 'GND', 16: 'DIGI_UPDI', 2: 'DIGI_CLK_MCU',
           3: 'DIGI_DATA_MCU', 4: 'DIGI_REQ_DRV', 11: 'SCL', 10: 'SDA', 5: None, 6: None, 7: None, 8: None,
           9: None, 12: None, 13: None, 14: None, 15: None, 17: None, 18: None, 19: None})
    b.C('100nF', '+3V3')
    b.CONN(3, 'UPDI', ['DIGI_UPDI', '+3V3', 'GND'], header(3))
    for n in ['DIGI_CLK', 'DIGI_DATA', 'DIGI_REQ']:
        b.TP(n)

    # ------------------------------------------------------------------ I/O and safety
    b.on(io)
    io.note('Expander outputs power up as inputs; 10 k pull-downs hold coils, stepper power and enables off until firmware drives them.')
    io.note('Stepper enable polarity is set in firmware after bench check 3. Any stepper alarm drops all motors (firmware).')
    exp1 = {21: 'GND', 2: 'GND', 3: 'GND', 1: 'EXP_INT_N', 22: 'SCL', 23: 'SDA', 24: '+3V3', 12: 'GND',
            4: 'COIL1_CMD', 5: 'COIL2_CMD', 6: 'COIL3_CMD', 7: 'COIL4_CMD', 8: 'COIL5_CMD', 9: 'COIL6_CMD',
            10: 'LAMP_CMD', 11: 'BLEED_PWR_EN', 13: 'BLEED_ENA', 14: 'ETH_RST_N', 15: 'ESTOP_OK_N',
            16: 'BLEED_HOME_N', 17: 'ORIF_B0_N', 18: 'ORIF_B1_N', 19: 'ORIF_B2_N', 20: 'SD_CD_N'}
    b.part('U', 'TCA9535PWR', 'TCA9535PWR #1 (0x20)', exp1)
    exp2 = {21: '+3V3', 2: 'GND', 3: 'GND', 1: 'EXP_INT_N', 22: 'SCL', 23: 'SDA', 24: '+3V3', 12: 'GND',
            4: 'LIFT_PWR_EN', 5: 'LIFT_ENA', 6: 'LIFT_ALM_N', 7: 'LIFT_HOME_N', 8: 'LIFT_MAX_N', 9: 'BLEED_ALM_N',
            10: 'ETH_INT_EXP', 11: 'EFUSE_FLT_N'}
    for i in range(8):
        exp2[13 + i] = 'EXP2_P1%d' % i
    b.part('U', 'TCA9535PWR', 'TCA9535PWR #2 (0x21)', exp2)
    b.C('100nF', '+3V3')
    b.C('100nF', '+3V3')
    b.R('10k', '+3V3', 'EXP_INT_N')
    for n in ['COIL%d_CMD' % i for i in range(1, 7)] + ['LAMP_CMD', 'BLEED_PWR_EN', 'LIFT_PWR_EN', 'BLEED_ENA', 'LIFT_ENA']:
        b.R('10k', n, 'GND')
    for n in ['ESTOP_OK_N', 'BLEED_HOME_N', 'ORIF_B0_N', 'ORIF_B1_N', 'ORIF_B2_N', 'LIFT_ALM_N', 'LIFT_HOME_N',
              'LIFT_MAX_N', 'BLEED_ALM_N', 'EFUSE_FLT_N', 'ETH_INT_EXP']:
        b.R('10k', '+3V3', n)
    b.CONN(10, 'Expander 2 spare', ['EXP2_P1%d' % i for i in range(8)] + ['+3V3', 'GND'], header(10))
    # opto inputs. TLP291-4 unit: anode, cathode, emitter, collector
    units = [(1, 2, 15, 16), (3, 4, 13, 14), (5, 6, 11, 12), (7, 8, 9, 10)]
    field24 = [('ESTOP_STAT_IN', 'ESTOP_OK_N'), ('BLEED_HOME_IN', 'BLEED_HOME_N'), ('LIFT_HOME_IN', 'LIFT_HOME_N'),
               ('LIFT_MAX_IN', 'LIFT_MAX_N'), ('ORIF_B0_IN', 'ORIF_B0_N'), ('ORIF_B1_IN', 'ORIF_B1_N'),
               ('ORIF_B2_IN', 'ORIF_B2_N')]
    alarms = [('BLEED', 'BLEED_ALM_N'), ('LIFT', 'LIFT_ALM_N')]
    chans = []
    for src, out in field24:
        b.R('4.7k', src, src + '_LED')          # about 5 mA from 24 V
        chans.append((src + '_LED', 'GND', out))
    for st, out in alarms:
        b.R('470R', '+5V', st + '_ALM_LED')      # iCL42 ALM is a normally open collector
        chans.append((st + '_ALM_LED', st + '_ALM_P', out))
    while len(chans) < 12:
        chans.append((None, None, None))
    for k in range(3):
        nets = {}
        for u, (a, c, e, col) in enumerate(units):
            an, ca, out = chans[4 * k + u]
            nets[a], nets[c] = an, ca
            nets[col], nets[e] = out, ('GND' if out else None)
        b.part('U', 'TLP291-4', 'TLP291-4', nets)
    # stepper line drivers
    for st in ['BLEED', 'LIFT']:
        b.part('U', 'AM26C31', 'AM26C31 (%s stepper)' % st.lower(), {1: st + '_STEP', 7: st + '_DIR', 9: st + '_ENA',
               15: 'GND', 4: '+5V', 12: 'GND', 2: st + '_PUL_P', 3: st + '_PUL_N', 6: st + '_DIR_P', 5: st + '_DIR_N',
               10: st + '_ENA_P', 11: st + '_ENA_N', 14: None, 13: None, 16: '+5V', 8: 'GND'})
        b.C('100nF', '+5V')
        b.CONN(8, '%s stepper signals (GX16-8)' % st.title(), [st + '_PUL_P', st + '_PUL_N', st + '_DIR_P',
               st + '_DIR_N', st + '_ENA_P', st + '_ENA_N', st + '_ALM_P', 'GND'], mc(8))
        b.CONN(2, '%s stepper 24 V (GX12-2)' % st.title(), [st + '_24V_F', 'GND'], mstb(2))
    # coil driver, lamp, E-stop
    b.part('U', 'TBD62083AFWG', 'TBD62083AFWG', {1: 'COIL1_CMD', 2: 'COIL2_CMD', 3: 'COIL3_CMD', 4: 'COIL4_CMD',
           5: 'COIL5_CMD', 6: 'COIL6_CMD', 7: 'LAMP_CMD', 8: 'GND', 9: 'GND', 10: 'COIL_24V_ESTOP',
           18: 'COIL1_RET', 17: 'COIL2_RET', 16: 'COIL3_RET', 15: 'COIL4_RET', 14: 'COIL5_RET', 13: 'COIL6_RET',
           12: 'LAMP_RET', 11: None})
    b.CONN(8, 'Motor housing coils (GX16-8)', ['COIL_24V_ESTOP'] + ['COIL%d_RET' % i for i in range(1, 7)] + [None], mc(8))
    b.CONN(2, 'Motors-armed lamp', ['COIL_24V_ESTOP', 'LAMP_RET'], mc(2))
    b.CONN(4, 'E-stop (2 NC contacts)', ['COIL_24V', 'COIL_24V_ESTOP', '+24V_FIELD', 'ESTOP_STAT_IN'], mc(4))
    io.note('E-stop contact 1 sits in series with the watchdog-gated coil supply (J pins 1-2); contact 2 reports status (pins 3-4).')
    # watchdog
    io.note('Heartbeat watchdog: 74HCT123 retriggered by GPIO46. Q stays high while pulses arrive (period < ~0.2 s); otherwise the coil supply drops.')
    b.part('U', '74HCT123', '74HCT123', {1: 'GND', 2: 'HEARTBEAT', 3: '+5V', 13: 'WD_OK', 4: None, 14: 'WD_CEXT',
           15: 'WD_RC', 9: '+5V', 10: 'GND', 11: 'GND', 5: None, 12: None, 6: None, 7: None, 16: '+5V', 8: 'GND'})
    b.R('220k', '+5V', 'WD_RC')
    b.part('C', 'C', '2.2uF film/C0G-X7R', {1: 'WD_RC', 2: 'WD_CEXT'}, footprint=FP['C1206'])
    b.C('100nF', '+5V')
    b.TP('WD_OK')

    nets, problems = p.check()
    return p, nets, problems


# =============================================================================== power module

def power_module(libdir):
    p = Project('flowbench-power-module', 'DIY Flow Bench V2 input power module (PM1), rev A', date=DATE)
    S = symbols.load(p, libdir)
    b = Builder(p, S)
    sh = Sheet('Power module', 'power-module.kicad_sch', 'PM1: TPS26631 eFuse with reverse blocking, TPS7A4901 analog 5 V', paper='A3')
    p.sheets = [sh]
    b.on(sh)
    sh.note('Plugs into the main board on two 2.54 mm headers. Power pins: 4 per rail, about 3 A each.')
    sh.note('eFuse settings: OVP 31.8 V (255k/10k), current limit 6.0 A (3.01k), UVLO default 15.5 V, about 11 ms soft start at 24 V (22 nF).')
    sh.note('MODE open = latch-off after an overload (default). Close JP to GND for auto-retry. SHDN left open (internal pull-up).')
    sh.note('PGTH and PGOOD are tied to GND (power-good unused; TI allows PGOOD at GND). FLT and IMON go to the main board.')
    sh.note('Reverse polarity: Q1 blocks it (TI arrangement: Q1 source to IN_SYS, drain to IN, gate to B_GATE; Q2 pulls B_GATE down).')
    sh.note('TVS SMCJ51CA: stays off with a 48 V supply plugged in by mistake; the eFuse OVP disconnects the board.')
    b.CONN(12, 'Power header', ['VIN_SUPPLY'] * 4 + ['GND'] * 4 + ['+24V'] * 4, header(12))
    b.CONN(6, 'Signal header', ['+12V', '+5VA', 'GND', 'FLT_N', 'IMON', 'GND'], header(6))
    b.part('D', 'D_TVS', 'SMCJ51CA', {1: 'VIN_SUPPLY', 2: 'GND'}, footprint=FP['SMC'])
    b.C('1uF 100V', 'VIN_SUPPLY', fp=FP['C1210'])
    b.part('Q', 'Q_NMOS_GDS', 'N-ch >=80 V, Rds(on) <=15 mOhm at 10 V (DPAK)', {1: 'B_GATE', 2: 'IN_PROT', 3: 'VIN_SUPPLY'},
           footprint=FP['DPAK'], fields={'Function': 'Q1 reverse blocking (TI example CSD19537Q3)'})
    b.part('Q', 'Q_NMOS_GSD', 'BSS138', {1: 'DRV', 2: 'VIN_SUPPLY', 3: 'B_GATE'}, footprint=FP['SOT23'],
           fields={'Function': 'Q2 B_GATE pull-down'})
    b.part('U', 'TPS26631PWP', 'TPS26631PWP', {1: 'IN_PROT', 2: 'IN_PROT', 3: 'IN_PROT', 4: 'B_GATE', 5: 'DRV',
           6: 'VIN_SUPPLY', 7: 'GND', 8: 'OVP', 9: 'GND', 10: 'DVDT', 11: 'ILIM', 12: 'MODE', 13: None, 14: 'IMON',
           15: 'FLT_N', 16: 'GND', 17: 'GND', 18: '+24V', 19: '+24V', 20: '+24V', 21: 'GND'})
    b.R('255k', 'IN_PROT', 'OVP')
    b.R('10k', 'OVP', 'GND')
    b.R('3.01k', 'ILIM', 'GND')
    b.C('22nF', 'DVDT')
    b.R('10k', 'IMON', 'GND')
    b.part('JP', 'SolderJumper_2_Open', 'MODE auto-retry', {1: 'MODE', 2: 'GND'}, footprint=FP['JP2O'])
    b.C('10uF 50V', 'IN_PROT', fp=FP['C1210'])
    b.CP('100uF 50V', '+24V', fp=FP['CELEC'])
    b.C('10uF 50V', '+24V', fp=FP['C1210'])
    sh.note('TPS7A4901: +5VA = 1.185 V x (1 + 32.4k/10k) = 5.02 V. 10 nF on NR/SS and across the top resistor (CFF).')
    b.part('U', 'TPS7A4901', 'TPS7A4901DGN', {8: '+12V', 5: '+12V', 6: 'NR_SS', 3: None, 7: None, 1: '+5VA', 2: 'FB5',
           4: 'GND', 9: 'GND'})
    b.C('10uF', '+12V', fp=FP['C1206'])
    b.C('10nF', 'NR_SS')
    b.R('32.4k', '+5VA', 'FB5')
    b.R('10k', 'FB5', 'GND')
    b.part('C', 'C', '10nF', {1: '+5VA', 2: 'FB5'}, footprint=FP['C'])
    b.C('10uF', '+5VA', fp=FP['C1206'])
    # PWR_FLAG only where no device output drives the net (+24V and +5VA are driven by U1 and U2)
    for n in ['VIN_SUPPLY', 'IN_PROT', '+12V', 'GND']:
        b.FLAG(n)
    for n in ['IN_PROT', '+24V', '+5VA', 'GND', 'FLT_N', 'IMON']:
        b.TP(n)
    nets, problems = p.check()
    return p, nets, problems


if __name__ == '__main__':
    libdir, outdir = sys.argv[1], sys.argv[2]
    ok = True
    for fn in (main_board, power_module):
        proj, nets, problems = fn(libdir)
        d = os.path.join(outdir, proj.name)
        proj.write(d)
        with open(os.path.join(d, 'netlist.csv'), 'w') as fh:
            fh.write('net,ref,pin,pin_name,sheet\n')
            for n in sorted(nets):
                for m in sorted(nets[n]):
                    fh.write('%s,%s,%s,%s,%s\n' % (n, m[0], m[1], m[2], m[3]))
        parts = sum(len(s.parts) for s in proj.sheets)
        print('%s: %d sheets, %d parts, %d nets' % (proj.name, len(proj.sheets), parts, len(nets)))
        for pr in problems:
            print('  PROBLEM', pr); ok = False
    sys.exit(0 if ok else 1)

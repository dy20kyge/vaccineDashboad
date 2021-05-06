import matplotlib as mp
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import requests
import csv
import math
import datetime
from datetime import datetime
from datetime import timedelta

factor_exp = 0.2
main_path = './pictures/'

group1 = 8600000#6000000#8600000
global vaccinated
global full_vaccinated
global newDoses
global dateVal
group2 = 13300000#16000000#12400000
group3 = 15400000#12000000#16300000
group4 = 17000000#46000000

global impfbereitschaft, impfbereitschaft_g1, impfbereitschaft_g2
impfbereitschaft_g1 = 0.9
impfbereitschaft_g2 = 0.9
impfbereitschaft = 0.75


font_date_axis = {'family' : 'DejaVu Sans',
        'weight' : 'bold',
        'size'   : 8}

def lastRow(row):
    global vaccinated
    vaccinated = int(row[8])
    global full_vaccinated
    full_vaccinated = int(row[9])

def download_impfdashboard_de():
    url = 'https://impfdashboard.de/static/data/germany_vaccinations_timeseries_v2.tsv'
    req = requests.get(url, allow_redirects=True)
    open(main_path + 'rawData.tsv', 'wb').write(req.content)


def reformat_newDoses():
    global newDoses, dateVal
    rawDataFile = open(main_path + 'rawData.tsv')
    read_rawDataFile = csv.reader(rawDataFile, delimiter='\t')
    lineNumber = 0
    # Alle Daten

    # Datum
    dateVal = []
    # Neue Dosen
    newDoses = []
    newDoses_exp = []
    avg_newDoses_list = []
    newDoses_exp_val = 0.0
    for row in read_rawDataFile:
        if lineNumber == 0:
            # Beschreibung ist unwichtig
            # pass
            print(row)
        else:
            # Daten fuellen
            dateVal.append(row[0])
            newDoses.append(int(row[2]))
            if newDoses_exp_val == 0:
                newDoses_exp_val = float(row[2])
                newDoses_exp.append(newDoses_exp_val)
            else:
                # 1.Grad newDoses_exp_val = (factor_exp * float(row[2])) + ((1-factor_exp) * newDoses_exp_val)
                newDoses_exp_val = factor_exp * (float(row[2]) - newDoses_exp_val) + newDoses_exp_val
            newDoses_exp.append(newDoses_exp_val)

            # Dashboard
            avg_newDoses = sum(newDoses[-7:])
            avg_newDoses = math.floor(avg_newDoses / 7)
            avg_newDoses_list.append(avg_newDoses)


            lastRow(row)


        lineNumber += 1


#Convert to np-arrays
    date_array = np.array(dateVal)
    newDoses_array = np.array(newDoses)
    avg_newDoses_array = np.array(avg_newDoses_list)
    np.savez_compressed(main_path + 'data', date=date_array, new=newDoses_array, new_exp=newDoses_exp, new_avg=avg_newDoses_array)

    #print(avg_newDoses)


def draw_diagrams_newDoses():
    months = mdates.MonthLocator()
    days = mdates.DayLocator()
    from matplotlib.pyplot import figure
    mp.rc('font', **font_date_axis)
    data = np.load(main_path + 'data.npz')

    fig, ax = plt.subplots()
    ax.plot('date', 'new', 'new_exp', data=data)
    ax.plot('date', 'new_avg', data=data)
    ax.format_xdata = mdates.DateFormatter('%d.%m.%Y')
    ax.grid(True)
    ax.legend()
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_minor_locator(days)
    fig.autofmt_xdate()
    plt.savefig(main_path + 'neueDosen.png', bbox_inches='tight')
    #plt.show()

def draw_diagram_phases():
    global  impfbereitschaft, vaccinated, full_vaccinated, impfbereitschaft_g1, impfbereitschaft_g2
    fig, ax =plt.subplots()
    phases = ("Phase 1", "Phase 2", "Phase 3", "Phase 4")
    phases_no_dose = [group1*impfbereitschaft_g1, group2*impfbereitschaft_g2, group3*impfbereitschaft, group4*impfbereitschaft]
    phases_first_dose = [0, 0, 0, 0]
    phases_second_dose = [0, 0, 0, 0]

    for i in range(4):
        if phases_no_dose[i] < vaccinated:
            phases_first_dose[i] = phases_no_dose[i]
            phases_no_dose[i] = 0
            vaccinated = vaccinated - phases_first_dose[i]
        else:
            phases_no_dose[i] = phases_no_dose[i] - vaccinated
            phases_first_dose[i] = vaccinated
            vaccinated = i
        if phases_first_dose[i] < full_vaccinated:
            full_vaccinated = full_vaccinated - phases_first_dose[i]
            phases_second_dose[i] = phases_first_dose[i]
            phases_first_dose[i] = 0
        else:
            phases_second_dose[i] = full_vaccinated
            phases_first_dose[i] = phases_first_dose[i] - full_vaccinated
            full_vaccinated = 0

    print(phases_no_dose)
    print(phases_first_dose)
    print(phases_second_dose)

    phases_pass = [group1*(1-impfbereitschaft_g1), group2*(1-impfbereitschaft_g2), group3*(1-impfbereitschaft), group4*(1-impfbereitschaft)]

    y_pos = np.arange(len(phases))
    colour = ['#050505', '#050505', '#050505', '#050505']
    plt.title('Impffortschritt in Millionen')
    plt.bar(y_pos, phases_second_dose, color='green', align='center')
    plt.bar(y_pos, phases_first_dose, color='yellow', bottom=phases_second_dose, align='center')
    plt.bar(y_pos, phases_no_dose, align='center', alpha=0.7, color='grey', bottom=[sum(data) for data in zip(phases_first_dose, phases_second_dose)])
    plt.bar(y_pos, phases_pass, align='center', alpha=0.15, color='grey',
            bottom=[sum(data) for data in zip(phases_first_dose, phases_second_dose, phases_no_dose)])
    ax.set_xticks(range(len(phases)))
    ax.set_xticklabels(phases, rotation='horizontal')
    scale = []
    for i in range(18):
        scale.append(i*1000000)
    scaleMio = []
    for i in range(18):
        scaleMio.append(i)
    ax.set_yticks(scale)
    ax.set_yticklabels(scaleMio)

    plt.savefig(main_path + 'fortschritt.png', bbox_inches='tight')
    #plt.show()

def draw_diagram_bar_records(): #blau kein Rekord, grün tagesrekord, lila gesamtrekord
    global newDoses, dateVal
    months = mdates.MonthLocator()
    days = mdates.DayLocator()
    from matplotlib.pyplot import figure
    mp.rc('font', **font_date_axis)
    fig, ax = plt.subplots()

    wochentag_record = [0, 0, 0, 0, 0, 0, 0]
    dates = []
    values = []
    colors = []
    record = 0
    tag = 6
    j = 0
    for i in range(len(newDoses)):
        dates.append(datetime.strptime(dateVal[i], '%Y-%m-%d').strftime("%d.%m"))
        tageswert = newDoses[i]
        values.append(tageswert)
        if wochentag_record[tag] < tageswert:
            if record < tageswert:
                record = tageswert
                colors.append('purple')
            else:
                colors.append('green')
            wochentag_record[tag] = tageswert
        else:
            colors.append('blue')
        tag = (tag+1) % 7
        if tag == 0:
            dates.append(" "*j)
            j = j+1
            values.append(0)
            colors.append('black')
    plt.figure(figsize=(18,7))
    plt.xticks(rotation=90)
    plt.grid(axis="y")
    plt.bar(dates, values, color=colors)
    # ax.grid(True)
    # ax.legend()
    # ax.xaxis.set_major_locator(months)
    # ax.xaxis.set_minor_locator(days)


    plt.savefig(main_path + 'neueDosenRekord.png', bbox_inches='tight')
    #plt.show()

def draw_diagram_line_days_to_finish():
    global newDoses, dateVal
    months = mdates.MonthLocator()
    days = mdates.DayLocator()
    from matplotlib.pyplot import figure
    mp.rc('font', **font_date_axis)
    data = np.load(main_path + 'data.npz')

    fig, ax = plt.subplots()
    dates = []
    values = []
    sevenDayAvg = [0, 0, 0, 0, 0, 0, 0]
    tag = 0
    totalDoses = 0
    j = 0

    for i in range(len(newDoses)):
        dates.append(datetime.strptime(dateVal[i], '%Y-%m-%d').strftime("%d.%m"))
        sevenDayAvg[tag] = newDoses[i]
        totalDoses = totalDoses + newDoses[i]
        tag = (tag + 1) % 7
        values.append((100000000 - totalDoses)/(sum(sevenDayAvg)/7))
        if j < 6:
            dates.pop(0)
            values.pop(0)
            j = j + 1
    plt.figure(figsize=(18, 7))
    plt.xticks(rotation=90)
    plt.grid(axis="y")
    plt.plot(dates, values)

    ax.format_xdata = mdates.DateFormatter('%d.%m.%Y')
    ax.grid(True)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_minor_locator(days)
    fig.autofmt_xdate()
    plt.savefig(main_path + 'daysToEnd.png', bbox_inches='tight')

def draw_diagram_line_days_to_finish_last_month():
    global newDoses, dateVal
    months = mdates.MonthLocator()
    days = mdates.DayLocator()
    from matplotlib.pyplot import figure
    mp.rc('font', **font_date_axis)
    data = np.load(main_path + 'data.npz')

    fig, ax = plt.subplots()
    dates = []
    values = []
    sevenDayAvg = [0, 0, 0, 0, 0, 0, 0]
    tag = 0
    totalDoses = 0
    j = 0

    for i in range(len(newDoses) - 37, len(newDoses)):
        dates.append(datetime.strptime(dateVal[i], '%Y-%m-%d').strftime("%d.%m"))
        sevenDayAvg[tag] = newDoses[i]
        totalDoses = totalDoses + newDoses[i]
        tag = (tag + 1) % 7
        values.append((100000000 - totalDoses) / (sum(sevenDayAvg) / 7))
        if j < 6:
            dates.pop(0)
            values.pop(0)
            j = j + 1


    plt.plot(dates, values)

    ax.format_xdata = mdates.DateFormatter('%d.%m.%Y')
    ax.grid(True)
    ax.xaxis.set_major_locator(days)
    fig.autofmt_xdate()
    plt.savefig(main_path + 'daysToEndMonth.png', bbox_inches='tight')


def draw_diagram_line_days_to_finish_last_month_dates():
    global newDoses, dateVal
    months = mdates.MonthLocator()
    days = mdates.DayLocator()
    weeks = mdates.WeekdayLocator()
    from matplotlib.pyplot import figure
    mp.rc('font', **font_date_axis)
    data = np.load(main_path + 'data.npz')

    fig, ax = plt.subplots()
    dates = []
    values = []
    todayValues = []
    sevenDayAvg = [0, 0, 0, 0, 0, 0, 0]
    tag = 0
    totalDoses = 0
    j = 0

    for i in range(len(newDoses) - 37, len(newDoses)):
        dates.append(datetime.strptime(dateVal[i], '%Y-%m-%d').strftime("%d.%m"))
        sevenDayAvg[tag] = newDoses[i]
        totalDoses = totalDoses + newDoses[i]
        tag = (tag + 1) % 7
        tmp = (100000000 - totalDoses) / (sum(sevenDayAvg) / 7)
        tmp2 = datetime.strptime(dateVal[i], '%Y-%m-%d') + timedelta(days=tmp)
        values.append(tmp2)
        todayValues.append(datetime.strptime(dateVal[i], '%Y-%m-%d'))
        if j < 6:
            dates.pop(0)
            values.pop(0)
            todayValues.pop(0)
            j = j + 1


    plt.plot(dates, values, todayValues)

    ax.format_xdata = mdates.DateFormatter('%d.%m.%Y')
    ax.grid(True, which='major', color='grey')
    ax.xaxis.set_major_locator(days)
    ax.yaxis.set_major_locator(months)
    plt.xticks(rotation=60)
    plt.savefig(main_path + 'daysToEndBest.png', bbox_inches='tight')
    ax.yaxis.set_minor_locator(weeks)
    ax.grid(True, which='minor', color='lightgrey')
    plt.savefig(main_path + 'daysToEndBest_alt.png', bbox_inches='tight')
    #plt.show()

if __name__ == '__main__':
    download_impfdashboard_de()
    reformat_newDoses()
    draw_diagrams_newDoses()
    draw_diagram_phases()
    draw_diagram_bar_records()
    draw_diagram_line_days_to_finish()
    draw_diagram_line_days_to_finish_last_month()
    draw_diagram_line_days_to_finish_last_month_dates()


#Ideen: Hochrechnung basierend auf 1. Impfung
#Ideen: Hochrechnung basierend auf 2. Impfung
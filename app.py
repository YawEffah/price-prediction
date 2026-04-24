# -*- coding: utf-8 -*-
from flask import Flask, render_template, send_file
from flask_cors import CORS, cross_origin
import numpy as np
import pandas as pd
from datetime import datetime
import crops
import random
import os

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/ticker": {"origins": "*"}})

commodity_dict = {}
gh_data_dir = "static/gh_data"
if os.path.exists(gh_data_dir):
    for filename in os.listdir(gh_data_dir):
        if filename.endswith(".csv"):
            name = filename.replace(".csv", "")
            commodity_dict[name] = os.path.join(gh_data_dir, filename)

# National monthly average rainfall for Ghana (mm)
annual_rainfall = [15, 30, 80, 140, 180, 200, 120, 80, 150, 150, 50, 20]

# Base price for Ghanaian crops is set to 100 because the CSVs contain actual prices
base = {name.capitalize(): 100 for name in commodity_dict.keys()}

commodity_list = []

def load_commodities():
    global commodity_list
    if not commodity_list:
        for name, path in commodity_dict.items():
            print(f"Loading {name}...")
            commodity_list.append(Commodity(path))

# Note: load_commodities() is called after the class definition below to avoid NameError

class Commodity:
    def __init__(self, csv_name):
        self.name = csv_name
        dataset = pd.read_csv(csv_name)
        self.X = dataset.iloc[:, :-1].values
        self.Y = dataset.iloc[:, 3].values

        from sklearn.tree import DecisionTreeRegressor
        depth = random.randrange(7, 18)
        self.regressor = DecisionTreeRegressor(max_depth=depth)
        self.regressor.fit(self.X, self.Y)

    def getPredictedValue(self, value):
        if value[1] >= 2024:
            fsa = np.array(value).reshape(1, 3)
            return self.regressor.predict(fsa)[0]
        else:
            # Historical lookup for data <= 2023
            fsa = [value[0], value[1]]
            # Find the index where Month and Year match
            # This is more robust than a linear sweep if we convert to list
            found = False
            for i in range(len(self.X)):
                if int(self.X[i][0]) == int(fsa[0]) and int(self.X[i][1]) == int(fsa[1]):
                    return self.Y[i]
            
            # If not found in historical, fall back to prediction
            fsa = np.array(value).reshape(1, 3)
            return self.regressor.predict(fsa)[0]

    def getCropName(self):
        # Extract filename without extension and directory
        return os.path.basename(self.name).replace(".csv", "")

# Load on startup
load_commodities()

@app.route('/')
def index():
    context = {
        "top5": TopFiveWinners(),
        "bottom5": TopFiveLosers(),
        "sixmonths": SixMonthsForecast()
    }
    return render_template('index.html', context=context, commodity_dict=commodity_dict)

@app.route('/historical')
def historical():
    summary = get_historical_summary()
    return render_template('historical.html', summary=summary)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/download/full')
def download_full():
    path = "scratch/wfp_food_prices_gha.csv"
    return send_file(path, as_attachment=True)

@app.route('/commodity/<name>')
def crop_profile(name):
    max_crop, min_crop, forecast_crop_values = TwelveMonthsForecast(name)
    # Get historical accuracy data (last 24 months of available actual data)
    accuracy_data = HistoricalAccuracyData(name)
    
    forecast_x = [i[0] for i in forecast_crop_values]
    forecast_y = [i[1] for i in forecast_crop_values]
    
    current_price = CurrentMonth(name)
    crop_data = crops.crop(name)
    
    context = {
        "name": name,
        "max_crop": max_crop,
        "min_crop": min_crop,
        "forecast_values": forecast_crop_values,
        "forecast_x": str(forecast_x),
        "forecast_y": forecast_y,
        "historical_accuracy": accuracy_data,
        "current_price": current_price,
        "image_url": crop_data[0],
        "prime_loc": crop_data[1],
        "type_c": crop_data[2],
        "export": crop_data[3]
    }
    return render_template('commodity.html', context=context)

@app.route('/api/forecast/<name>')
def api_forecast(name):
    from flask import request, jsonify
    months = int(request.args.get('months', 12))
    max_crop, min_crop, forecast_values = TwelveMonthsForecast(name, months=months)
    
    # Format table rows for the frontend
    table_html = ""
    for item in forecast_values:
        change_class = "text-emerald-600 bg-emerald-50" if item[2] >= 0 else "text-rose-600 bg-rose-50"
        change_icon = "ph-caret-up" if item[2] >= 0 else "ph-caret-down"
        change_prefix = "+" if item[2] >= 0 else ""
        
        table_html += f"""
        <tr class="hover:bg-slate-50/50 transition-colors">
            <td class="px-6 py-4 font-semibold text-slate-700">{item[0]}</td>
            <td class="px-6 py-4 text-right font-medium text-slate-600">GH₵ {item[1]}</td>
            <td class="px-6 py-4 text-right">
                <div class="inline-flex items-center gap-1 font-bold px-2.5 py-1 rounded-lg text-sm {change_class}">
                    <span>{change_prefix}{item[2]}%</span>
                    <i class="ph-bold {change_icon}"></i>
                </div>
            </td>
        </tr>
        """

    return jsonify({
        "forecast_x": [i[0] for i in forecast_values],
        "forecast_y": [i[1] for i in forecast_values],
        "max_price": max_crop[1],
        "max_month": max_crop[0],
        "min_price": min_crop[1],
        "min_month": min_crop[0],
        "table_html": table_html
    })

@app.route('/ticker/<item>/<number>')
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def ticker(item, number):
    n = int(number)
    i = int(item)
    data = SixMonthsForecast()
    context = str(data[n][i])

    if i == 2 or i == 5:
        context = 'GH₵' + context
    elif i == 3 or i == 6:
        context = context + '%'
    return context

def get_historical_summary():
    summary = []
    for name, path in commodity_dict.items():
        df = pd.read_csv(path)
        min_p = df['WPI'].min()
        max_p = df['WPI'].max()
        avg_p = df['WPI'].mean()
        start_year = df['Year'].min()
        end_year = df['Year'].max()
        # Calculate variance as a crude volatility indicator
        # High-low spread relative to average
        volatility = ((max_p - min_p) / avg_p) * 100 if avg_p != 0 else 0
        
        summary.append({
            "name": name.replace('_', ' ').capitalize(),
            "id": name,
            "min": round(float(min_p), 2),
            "max": round(float(max_p), 2),
            "avg": round(float(avg_p), 2),
            "volatility": round(float(volatility), 1),
            "coverage": f"{start_year} - {end_year}"
        })
    return summary

def TopFiveWinners():
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    prev_rainfall = annual_rainfall[prev_month - 1]
    
    current_month_prediction = []
    prev_month_prediction = []
    change = []

    for i, comm in enumerate(commodity_list):
        current_predict = comm.getPredictedValue([float(current_month), current_year, current_rainfall])
        current_month_prediction.append(current_predict)
        prev_predict = comm.getPredictedValue([float(prev_month), prev_year, prev_rainfall])
        prev_month_prediction.append(prev_predict)
        if prev_predict == 0: prev_predict = 1 # Avoid division by zero
        change.append((((current_predict - prev_predict) * 100 / prev_predict), i))
    
    sorted_change = sorted(change, key=lambda x: x[0], reverse=True)
    to_send = []
    for j in range(0, min(5, len(sorted_change))):
        perc, i = sorted_change[j]
        name = commodity_list[i].getCropName()
        to_send.append([name.replace('_', ' ').capitalize(), round(current_month_prediction[i], 2), round(perc, 2)])
    return to_send

def TopFiveLosers():
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    prev_rainfall = annual_rainfall[prev_month - 1]
    
    current_month_prediction = []
    prev_month_prediction = []
    change = []

    for i, comm in enumerate(commodity_list):
        current_predict = comm.getPredictedValue([float(current_month), current_year, current_rainfall])
        current_month_prediction.append(current_predict)
        prev_predict = comm.getPredictedValue([float(prev_month), prev_year, prev_rainfall])
        prev_month_prediction.append(prev_predict)
        if prev_predict == 0: prev_predict = 1
        change.append((((current_predict - prev_predict) * 100 / prev_predict), i))
    
    sorted_change = sorted(change, key=lambda x: x[0])
    to_send = []
    for j in range(0, min(5, len(sorted_change))):
        perc, i = sorted_change[j]
        name = commodity_list[i].getCropName()
        to_send.append([name.replace('_', ' ').capitalize(), round(current_month_prediction[i], 2), round(perc, 2)])
    return to_send

def SixMonthsForecast():
    month_data = [[] for _ in range(6)]
    for comm in commodity_list:
        crop_forecast = SixMonthsForecastHelper(comm.getCropName())
        for k, (time, price, change) in enumerate(crop_forecast):
            month_data[k].append((price, change, comm.getCropName().replace('_', ' ').capitalize(), time))
    
    for m in month_data:
        m.sort()
        
    crop_month_wise = []
    for m in month_data:
        if not m: continue
        crop_month_wise.append([
            m[0][3], # Time
            m[-1][2], # Winner Name
            m[-1][0], # Winner Price
            m[-1][1], # Winner Change
            m[0][2], # Loser Name
            m[0][0], # Loser Price
            m[0][1]  # Loser Change
        ])
    return crop_month_wise

def SixMonthsForecastHelper(name):
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    
    commodity = next((c for c in commodity_list if c.getCropName() == name), commodity_list[0])
    
    month_with_year = []
    for i in range(1, 7):
        m = current_month + i
        y = current_year
        if m > 12:
            m -= 12
            y += 1
        month_with_year.append((m, y, annual_rainfall[m - 1]))
        
    current_price = commodity.getPredictedValue([float(current_month), current_year, current_rainfall])
    if current_price == 0: current_price = 1
    
    crop_price = []
    for m, y, r in month_with_year:
        pred = commodity.getPredictedValue([float(m), y, r])
        change = ((pred - current_price) * 100) / current_price
        time_str = datetime(y, m, 1).strftime("%b %y")
        crop_price.append([time_str, round(pred, 2), round(change, 2)])
    return crop_price

def CurrentMonth(name):
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    
    commodity = next((c for c in commodity_list if c.getCropName() == name), commodity_list[0])
    current_price = commodity.getPredictedValue([float(current_month), current_year, current_rainfall])
    return round(float(current_price), 3)

def TwelveMonthsForecast(name, months=12):
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_rainfall = annual_rainfall[current_month - 1]
    
    commodity = next((c for c in commodity_list if c.getCropName() == name), commodity_list[0])
    
    month_with_year = []
    for i in range(1, months + 1):
        m = current_month + i
        y = current_year
        while m > 12:
            m -= 12
            y += 1
        month_with_year.append((m, y, annual_rainfall[m - 1]))
        
    wpis = []
    current_price = commodity.getPredictedValue([float(current_month), current_year, current_rainfall])
    if current_price == 0: current_price = 1
    
    for m, y, r in month_with_year:
        wpis.append(commodity.getPredictedValue([float(m), y, r]))
        
    crop_price = []
    max_val = -1
    min_val = 1e9
    max_idx = 0
    min_idx = 0
    
    for i, pred in enumerate(wpis):
        if pred > max_val:
            max_val = pred
            max_idx = i
        if pred < min_val:
            min_val = pred
            min_idx = i
        
        m, y, r = month_with_year[i]
        change = ((pred - current_price) * 100) / current_price
        time_str = datetime(y, m, 1).strftime("%b %y")
        crop_price.append([time_str, round(float(pred), 2), round(float(change), 2)])
        
    max_crop = [crop_price[max_idx][0], round(float(max_val), 2)]
    min_crop = [crop_price[min_idx][0], round(float(min_val), 2)]
    
    return max_crop, min_crop, crop_price

def HistoricalAccuracyData(name):
    commodity = next((c for c in commodity_list if c.getCropName() == name), commodity_list[0])
    
    # Extract last 24 available months from X and Y
    # X columns: Month, Year, Rainfall
    # Y: WPI
    n_points = min(24, len(commodity.X))
    last_x = commodity.X[-n_points:]
    last_y = commodity.Y[-n_points:]
    
    labels = []
    actuals = []
    predicts = []
    errors = []
    
    for i in range(n_points):
        m, y, r = int(last_x[i][0]), int(last_x[i][1]), last_x[i][2]
        actual = last_y[i]
        
        # Force prediction instead of lookup for accuracy check
        pred = commodity.regressor.predict(np.array([float(m), float(y), r]).reshape(1, 3))[0]
        
        time_str = datetime(y, m, 1).strftime("%b %y")
        labels.append(time_str)
        actuals.append(round(float(actual), 2))
        predicts.append(round(float(pred), 2))
        
        # MAPE calculation part
        if actual != 0:
            errors.append(abs((float(actual) - float(pred)) / float(actual)))
            
    avg_error = np.mean(errors) if errors else 0
    accuracy = round((1 - float(avg_error)) * 100, 1)
    
    return {
        "labels": labels,
        "actuals": actuals,
        "predictions": predicts,
        "accuracy": accuracy
    }

def TwelveMonthPrevious(name):
    commodity = next((c for c in commodity_list if c.getCropName() == name), commodity_list[0])
    
    month_with_year = []
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    for i in range(1, 13):
        m = current_month - i
        y = current_year
        if m < 1:
            m += 12
            y -= 1
        month_with_year.append((m, y, annual_rainfall[m - 1]))
    
    # The original app uses a fixed year 2013 for previous data in some places, 
    # but we'll try to use actual previous year data if available.
    # However, for consistency with original hacky logic:
    crop_prev_price = []
    for m, y, r in reversed(month_with_year):
        # Using a year within our GH dataset range (2006-2021)
        # Let's just use the actual year we calculated
        try:
            pred = commodity.getPredictedValue([float(m), y, r])
        except:
            pred = 0
        time_str = datetime(y, m, 1).strftime("%b %y")
        crop_prev_price.append([time_str, round(pred, 2)])
        
    return crop_prev_price

if __name__ == "__main__":
    app.run(debug=True)

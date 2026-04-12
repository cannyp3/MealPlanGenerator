import csv
import json
import urllib.request
import urllib.error
import datetime
import random
import os
from dataclasses import dataclass

@dataclass
class Meal:
    name: str
    protein: str
    is_outside: bool
    is_mexican: bool

# Configuration for Stoneham, MA
LATITUDE = 42.4801
LONGITUDE = -71.0995
WEATHER_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&daily=temperature_2m_max,precipitation_sum,snowfall_sum,weather_code&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=America%2FNew_York&forecast_days=14"

MEALS_CSV = "MealOptions.csv"
OUTPUT_HTML = "index.html"

def get_weather_forecast():
    """Fetches weather forecast for the next 14 days with error handling."""
    try:
        # 10 second timeout for responsiveness
        with urllib.request.urlopen(WEATHER_API_URL, timeout=10) as response:
            if response.status != 200:
                print(f"Error: Weather API returned HTTP {response.status}")
                return None
                
            try:
                data = json.loads(response.read().decode())
            except json.JSONDecodeError:
                print("Error: Could not parse Weather API response (not valid JSON).")
                return None
                
            daily = data.get("daily", {})
            time_list = daily.get("time", [])
            temp_list = daily.get("temperature_2m_max", [])
            precip_list = daily.get("precipitation_sum", [])
            snow_list = daily.get("snowfall_sum", [])
            code_list = daily.get("weather_code", [])
            
            # Validation: check if all required data arrays have the same length
            if not time_list:
                print("Error: Weather API response missing 'time' data.")
                return None
                
            if not (len(time_list) == len(temp_list) == len(precip_list) == len(snow_list)):
                print("Warning: Weather API returned incomplete or mismatched data arrays.")
                # We can still proceed, but the data might be inaccurate
            
            forecast = {}
            for i, date_str in enumerate(time_list):
                try:
                    forecast[date_str] = {
                        "high_temp": temp_list[i] if i < len(temp_list) else "N/A",
                        "precip": (precip_list[i] if i < len(precip_list) else 0) + 
                                  (snow_list[i] if i < len(snow_list) else 0),
                        "code": code_list[i] if i < len(code_list) else None
                    }
                except (IndexError, TypeError):
                    forecast[date_str] = {"high_temp": "N/A", "precip": 0, "code": None}
            return forecast
            
    except urllib.error.HTTPError as e:
        print(f"Error: Weather API request failed (HTTP {e.code}: {e.reason})")
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to Weather API ({e.reason})")
    except TimeoutError:
        print("Error: Weather API request timed out.")
    except Exception as e:
        print(f"Error fetching weather: {type(e).__name__}: {e}")
    return None

def get_weather_desc(code):
    """Maps WMO weather code to simple descriptions."""
    if code is None: return "Unknown"
    # WMO Weather interpretation codes (WW)
    if code == 0: return "Sunny"
    if code in [1, 2, 3]: return "Mostly Sunny"
    if code in [45, 48]: return "Foggy"
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "Rainy"
    if code in [71, 73, 75, 77, 85, 86]: return "Snowy"
    if code in [95, 96, 99]: return "Stormy"
    return "Cloudy"

def load_meals():
    """Loads meals from CSV file with validation."""
    meals = []
    if not os.path.exists(MEALS_CSV):
        print(f"Error: {MEALS_CSV} not found. Please ensure it exists in the same directory.")
        return []
    
    required_headers = ["Meal Name", "Protein", "Outside", "Mexican"]
    
    try:
        with open(MEALS_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check for missing headers
            if not reader.fieldnames:
                print(f"Error: {MEALS_CSV} is empty or invalid.")
                return []
            
            missing = [h for h in required_headers if h not in reader.fieldnames]
            if missing:
                print(f"Error: {MEALS_CSV} is missing required columns: {', '.join(missing)}")
                return []

            for line_num, row in enumerate(reader, start=2):
                try:
                    name = row["Meal Name"].strip()
                    protein = row["Protein"].strip()
                    if not name or not protein:
                        print(f"Warning: Skipping row {line_num} due to missing name or protein.")
                        continue
                        
                    meals.append(Meal(
                        name=name,
                        protein=protein,
                        is_outside=row["Outside"].strip().lower() == "yes",
                        is_mexican=row["Mexican"].strip().lower() == "yes"
                    ))
                except KeyError as e:
                    print(f"Warning: Skipping row {line_num} due to missing column: {e}")
                except Exception as e:
                    print(f"Warning: Unexpected error on row {line_num}: {e}")
                    
    except Exception as e:
        print(f"Critical Error loading {MEALS_CSV}: {e}")
        return []
        
    if not meals:
        print(f"Warning: No valid meals found in {MEALS_CSV}.")
    return meals

def get_plan_dates():
    """Calculates the dates for the upcoming plan week starting Saturday."""
    today = datetime.date.today()
    days_ahead = (5 - today.weekday()) % 7
    start_date = today + datetime.timedelta(days=days_ahead)
    return [start_date + datetime.timedelta(days=i) for i in range(7)]

def generate_plan(meals, weather, dates):
    """Generates a single valid meal plan using recursive backtracking."""
    days_of_week = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Required categories for fixed slots
    fixed_slots = ["Leftovers", "Pizza", "Premade Meal / Takeout"]
    
    # Randomly assign fixed slots to 3 indices
    all_indices = list(range(7))
    random.shuffle(all_indices)
    fixed_indices = all_indices[:3]
    
    plan = [None] * 7
    for i, name in zip(fixed_indices, fixed_slots):
        plan[i] = Meal(name=name, protein="None", is_outside=False, is_mexican=False)
    
    remaining_indices = sorted(all_indices[3:])
    
    # Shuffle available meals to ensure variety across generated plans
    available_meals = list(meals)
    random.shuffle(available_meals)

    def is_locally_valid(meal: Meal, idx):
        """Checks constraints that only depend on the current meal and its neighbors."""
        # 1. Consecutive protein check
        for neighbor_idx in [idx - 1, idx + 1]:
            if 0 <= neighbor_idx < 7 and plan[neighbor_idx]:
                if meal.protein != "None" and meal.protein == plan[neighbor_idx].protein:
                    return False
        
        # 2. Weather check for outside meals
        if meal.is_outside:
            date_str = dates[idx].isoformat()
            w = weather.get(date_str, {})
            high = w.get("high_temp")
            precip = w.get("precip", 0)
            
            # If weather is missing or too cold/wet, don't cook outside
            if high == "N/A" or high is None or high <= 45 or precip > 0:
                return False
        return True

    def backtrack(step):
        """Recursive solver to fill remaining slots."""
        if step == len(remaining_indices):
            # Base Case: All slots filled. Now check global constraints.
            proteins = [m.protein for m in plan if m]
            has_pork = "Pork" in proteins
            has_chicken = "Chicken" in proteins
            has_beef_fish = "Beef" in proteins or "Fish" in proteins
            
            # Monday is index 2, Tuesday is index 3
            mon_tue_mexican = (plan[2] and plan[2].is_mexican) or (plan[3] and plan[3].is_mexican)
            
            return has_pork and has_chicken and has_beef_fish and mon_tue_mexican

        idx = remaining_indices[step]
        # Try each available meal for this slot
        for i in range(len(available_meals)):
            meal = available_meals[i]
            if is_locally_valid(meal, idx):
                plan[idx] = meal
                # Temporarily remove meal to avoid using it twice in the same plan
                used_meal = available_meals.pop(i)
                
                if backtrack(step + 1):
                    return True
                
                # Backtrack: restore meal and clear slot
                available_meals.insert(i, used_meal)
                plan[idx] = None
        return False

    if backtrack(0):
        return list(zip(days_of_week, dates, plan))
    return None

def generate_html(plans, weather, dates):
    """Generates an accessible HTML file with the meal plan options."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Weekly Meal Plan</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; line-height: 1.6; background-color: #000000; color: #ffffff; }}
        .container {{ max-width: 600px; margin: auto; background: #121212; padding: 30px; border-radius: 12px; border: 1px solid #333333; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
        h1 {{ text-align: center; color: #ffffff; margin-bottom: 5px; }}
        .subtitle {{ text-align: center; color: #b0b0b0; margin-bottom: 30px; font-size: 1em; }}
        .weather-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #121212; border-radius: 8px; overflow: hidden; border: 1px solid #333333; }}
        .weather-table th, .weather-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333333; }}
        .weather-table th {{ background-color: #1a1a1a; color: #ffffff; font-weight: 700; border-bottom: 2px solid #333333; }}
        .option {{ margin-bottom: 40px; padding: 25px; border: 1px solid #333333; border-radius: 12px; background-color: #1a1a1a; }}
        .option h2 {{ margin-top: 0; color: #ffffff; border-bottom: 1px solid #333333; padding-bottom: 10px; margin-bottom: 20px; }}
        .meal-list {{ list-style: none; padding: 0; margin: 0; }}
        .meal-item {{ margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px dashed #333333; font-size: 1.1em; }}
        .meal-item:last-child {{ border-bottom: none; }}
        .day-name {{ color: #ffffff; font-weight: 700; display: inline-block; }}
        @media (max-width: 480px) {{
            .container {{ padding: 15px; }}
            .day-name {{ display: block; margin-bottom: 4px; }}
        }}
        </style></head>
<body>
    <main class="container">
        <header>
            <h1>Dinner Menu</h1>
            <p class="subtitle">Weekly Plan for {dates[0].strftime('%B %d')} – {dates[-1].strftime('%d, %Y')}</p>
        </header>
        
        <section aria-labelledby="weather-heading">
            <h2 id="weather-heading" style="position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0;">Weekly Weather Forecast</h2>
            <table class="weather-table">
                <thead>
                    <tr>
                        <th scope="col">Day</th>
                        <th scope="col">High</th>
                        <th scope="col">Forecast</th>
                    </tr>
                </thead>
                <tbody>
"""
    for d in dates:
        date_str = d.isoformat()
        w = weather.get(date_str, {})
        high = w.get("high_temp", "N/A")
        desc = get_weather_desc(w.get("code"))
        day_name = d.strftime("%A")
        html_content += f"""
                    <tr>
                        <th scope="row">{day_name}</th>
                        <td>{high}°F</td>
                        <td>{desc}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </section>

        <section aria-label="Meal Plan Options">
"""
    if not plans:
        html_content += "<p role='alert'>Could not generate enough valid meal plans. Please check constraints or add more meal options.</p>"
    else:
        for i, plan in enumerate(plans):
            html_content += f"""
            <article class="option">
                <h2>Option {i+1}</h2>
                <ul class="meal-list">
"""
            for day_name, date, meal in plan:
                html_content += f"""
                    <li class="meal-item">
                        <span class="day-name">{day_name}:</span> 
                        <span>{meal.name}</span>
                    </li>
"""
            html_content += """
                </ul>
            </article>"""

    html_content += f"""
        </section>
        <footer style="text-align: center; margin-top: 40px; border-top: 1px solid #333333; padding-top: 20px;">
            <p style="font-size: 0.9em; color: #b0b0b0;">Generated on: {datetime.date.today().strftime('%B %d, %Y')}</p>
            <p style="font-size: 0.8em; color: #b0b0b0; margin-top: 5px;">&copy; {datetime.date.today().year} Meal Plan Generator</p>
        </footer>
    </main>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding='utf-8') as f:
        f.write(html_content)
    print(f"Generated {OUTPUT_HTML}")

def main():
    weather = get_weather_forecast()
    if not weather:
        print("Failed to get weather. Proceeding with caution (assuming all days > 45F and dry).")
        weather = {}
        
    meals = load_meals()
    if not meals:
        return

    dates = get_plan_dates()
    plans = []
    seen_plans = set()
    
    attempts = 0
    while len(plans) < 3 and attempts < 100:
        attempts += 1
        plan = generate_plan(meals, weather, dates)
        if plan:
            # Create a unique key for the plan to avoid duplicates
            plan_key = tuple(m.name for _, _, m in plan)
            if plan_key not in seen_plans:
                seen_plans.add(plan_key)
                plans.append(plan)
    
    if not plans:
        print("Final Error: No valid meal plans could be generated. This is likely due to restrictive constraints (e.g., weather) or lack of meal variety in your CSV.")
    
    generate_html(plans, weather, dates)

if __name__ == "__main__":
    main()

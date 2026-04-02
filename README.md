# 🍽️ Meal Plan Generator

A weather-aware automated meal planner that generates a 7-day dinner menu based on a rotating set of protein requirements, dietary constraints, and local weather forecasts.

## ✨ Features

- **Weather-Aware Planning:** Fetches a 14-day forecast from the Open-Meteo API. "Outside" meals (like grilling) are only scheduled on days where the high temperature is > 45°F and there is no precipitation.
- **Backtracking Algorithm:** Uses a recursive backtracking solver to ensure that all protein and category constraints are met across three unique plan options.
- **Balanced Nutrition:** Enforces specific weekly protein variety (e.g., at least one Pork, one Chicken, and one Beef or Fish).
- **Theme Nights:** Automatically ensures a "Mexican Night" occurs on either Monday or Tuesday.
- **Mobile-Responsive Output:** Generates a clean, modern `index.html` file with a weather summary table and three menu options.
- **Automated Updates:** Integrated with GitHub Actions to regenerate the plan every Thursday morning.

## 🛠️ Tech Stack

- **Python 3.x:** Core logic and data processing.
- **Open-Meteo API:** Free weather forecast data.
- **GitHub Actions:** Automated weekly generation and deployment to GitHub Pages.
- **Vanilla CSS:** Responsive styling for the output.

## 📋 Constraints & Logic

The generator fills 7 slots starting the next Saturday:
1.  **3 Fixed Slots:** Randomly assigns "Pizza", "Leftovers", and "Premade Meal / Takeout".
2.  **4 Variable Slots:** Filled from `MealOptions.csv` using the following rules:
    - **Protein Variety:** Every plan must include at least one Pork, one Chicken, and one Beef or Fish meal.
    - **No Repeats:** No consecutive days can have the same primary protein.
    - **Mexican Rule:** Either Monday or Tuesday must be a meal marked as "Mexican".
    - **Weather Safety:** Meals marked as "Outside" are automatically skipped if the forecast is cold or rainy.

## 🚀 Getting Started

### 1. Prepare your Meal Options
Edit `MealOptions.csv` to include your favorite meals. Use the following headers:
- `Meal Name`: The display name of the dish.
- `Protein`: (e.g., Beef, Chicken, Pork, Fish, Other).
- `Outside`: Set to `Yes` if this meal requires grilling/outdoor cooking.
- `Mexican`: Set to `Yes` if this meal satisfies the Mexican night requirement.

### 2. Run Locally
```bash
python3 meal_plan_generator.py
```
This will generate an `index.html` file in the root directory.

### 3. Deployment
The included `.github/workflows/generate_meal_plan.yml` will automatically:
- Run every Thursday.
- Generate a new `index.html`.
- Deploy the result to your repository's GitHub Pages.

## 📂 Project Structure
- `meal_plan_generator.py`: The main logic, solver, and HTML generator.
- `MealOptions.csv`: Your database of potential meals.
- `index.html`: The generated output (overwritten each run).
- `.github/workflows/`: Automation settings.

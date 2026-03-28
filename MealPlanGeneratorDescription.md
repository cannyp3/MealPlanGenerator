# Meal Plan Generator Project Description

I manually create a weekly dinner meal plan for my family and am looking to automate the process.

Help me create a simple Python script which generates a formatted web page. The script would by run via a GitHub Actions pipeline automatically every Thursday morning. I plan on hosting this on GitHub using GitHub Pages.

The script should take in meals from a set menu stored in a text file (I assume .csv would work?). Information for each meal would include: Meal Name, Protein, Outside, Mexican

"Meal Name" is a short name.

"Protein" is either Chicken, Beef, Pork, Fish, or Other

"Outside" is a simple "Yes" or "No". It denotes whether the meal can only be cooked outside on my gas grill or smoker.

"Mexican" is a simple "Yes" or "No". It denotes whether the meal is Mexican.

Ideally the script would query some free weather API to get the expected high temperature and weather for Stoneham, Massachusetts the following week. For any menu item where "Outside" is "Yes", the high temperature for that day would need to be above 45 degrees Fahrenheit with no snow or rain in the forecast.

Here are the rules to follow when generating a meal plan:

1. One night is "Leftovers"
2. One night is "Pizza"
3. One night is "Premade Meal / Takeout"
4. Consecutive nights cannot repeat a Protein
5. One night must have a Protein of "Pork"
6. One night must have a Protein of "Chicken"
7. One night must have a Protein of either "Beef" or "Fish"
8. Monday or Tuesday night must have a "Mexican" meal


The script would generate three different meal plan options for the following week.

Each meal plan must follow the following format:


**Saturday**: Grilled Fish

**Sunday**: Smoked Ribs

**Monday**: Rib Burritos

**Tuesday**: Pizza

**Wednesday**: Leftovers

**Thursday**: Premade Meal / Takeout

**Friday**: Sausage Skillet Meal


For that example meal plan, the Proteins were:

Grilled Fish: "Fish"
Smoked Ribs: "Pork"
Rib Burritos: "Pork" (with "Mexican" as "Yes")
Sausage Skillet Meal: "Pork"
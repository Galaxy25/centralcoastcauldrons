\# Strategy:



The biggest problem for this potion shop is deciding which potions should be sold on which days. I’m treating this problem as a multi-armed bandit problem and using UCB to solve it. 



I track for each day: which potions are shown and which are bought. These values can be used to calculate a UCB value, which can be used to prioritize which potions are sold. This is important because there are 36 different potion variants. These variants range in 25 increments of each color. 



I initially wanted to buy barrels and create a potion based on UCB. This took too much time to implement, so I went with color limits for barrels. The potion creation process is based on setting a potion type class + looping through each potion type that can be made and distributing the potions made evenly.


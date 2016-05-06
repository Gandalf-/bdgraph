# bdgraph
bdgraph is a tool for converting simply formatted files into handy graphviz dot files.
It's great for managing complicated projects where steps have multiple dependencies on
each other!

## Here's an example!
```
1 : Find a fallen log
2 : Find an ax
3 : Chop up the log
8 : Make kindling
10 : Make a fire

5 : Go to the store
4 : Buy ingredients
7 : Buy matches

9 : Make smores!

Options
	color_next
	color_complete

Dependencies
	3 -> 8
	7,8 -> 10
	1,2 -> 3
	5 -> 4
	5 -> 7
	4,10 -> 9
```
### Which creates the following:
```
digraph g{
	rankdir=LR;
	ratio = fill;
	node [style=filled];
	"Chop up\n the log" -> "Make\n kindling"
	"Buy\n matches" -> "Make a\n fire"
	"Make\n kindling" -> "Make a\n fire"
	"Find a\n fallen log" -> "Chop up\n the log"
	"Find\n an ax" -> "Chop up\n the log"
	"Go to the\n store" -> "Buy\n ingredients"
	"Go to the\n store" -> "Buy\n matches"
	"Buy\n ingredients" -> "Make\n smores!"
	"Make a\n fire" -> "Make\n smores!"
	"Find a\n fallen log"[color="0.499 0.386 1.000"];
	"Find\n an ax"[color="0.499 0.386 1.000"];
	"Chop up\n the log"
	"Make\n kindling"
	"Make a\n fire"
	"Go to the\n store"[color="0.499 0.386 1.000"];
	"Buy\n ingredients"
	"Buy\n matches"
	"Make\n smores!"
}
```
### What a mess! But now you can paste into a dot file viewer to get:

![Alt text](test/example1.png)

## Options
bdgraph has several *optional* options that you can enable by adding them to the options
section of your input file. Really, the whole options section is optional itself!
- color_complete: highlight nodes marked with '@' in gren

- color_urgent: highlight nodes marked with '!' in red

- color_next: highlight nodes that don't have any unmet dependencies in blue

- clean_up: tells bdgraph to reorganize your input file. It'll reorder the node labels
  so they're in order, but maintain your extra line breaks so you can keep nodes grouped
  together.

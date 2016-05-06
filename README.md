# bdgraph
bdgraph is a tool for converting simply formatted files into handy graphviz dot files.
It's great for managing complicated projects where steps have multiple dependencies on
each other!

![Alt text](test/example1.png)

## Options 
bdgraph has several *optional* options that you can enable by adding them to the options section of your input file. Really, the whole options section is optional itself!
- **color_complete**: highlight nodes marked with '@' in gren
- **color_urgent**: highlight nodes marked with '!' in red
- **color_next**: highlight nodes that don't have any unmet dependencies in blue
- **cleanup**: tells bdgraph to reorganize your input file. It'll reorder the node
  labels so they're in order, but maintain the node values themselves and your extra
  line breaks so you can keep nodes grouped together.

## Dependencies
The dependencies section tells bdgraph how your information is related. It uses a simple
syntax in which '1 -> 2' means '2' relies on '1'. What this means is up to you! I've
used it for relating references in papers and for to-do lists. Identation and spacing
are entirely optional.

### Here's an example!
```
1:  Find a fallen log
2:  Find an ax
3:  Chop up the log
4:  Make kindling
5:  Make a fire

6: @Go to the store
7:  Buy ingredients
8:  Buy matches

9:  Make smores!

options
  color_next
  color_complete

dependencies
  1,2 -> 3
  3 -> 4

  8,4 -> 5
  6 -> 7
  6 -> 8

  7,5 -> 9
```
### bdgraph uses this to generate the following:
Which you can then paste or open in any dot file viewer to get the nice image at the top!
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

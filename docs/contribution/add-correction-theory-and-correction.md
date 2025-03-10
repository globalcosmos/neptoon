## Creating your own corrections factory

- Once tested you want to write a branch ready to be included to neptoon
- Branch out from development (link key contribution document)
- To add a correction we must update these parts:
	  - Theory
	  - Correction Class/Factory
	  - CorrectionTheory Enum
	  - SiteInformation (OPTIONAL)
	  - ColumnInfo (OPTIONAL)

### Theory Structure

- Units (link)
- 

### Before we start

- Expect a new column of data? Update COLUMNINFO (link)
- New static variables? Update SiteInformation
	- SiteInfo will be converted to a column in your df (roving)

### Correction Class Structure

- Describe the super class
- Expected output style
- How to build (with example)

### Putting it all together

- add theory to the corrections.__init__.py file
- 
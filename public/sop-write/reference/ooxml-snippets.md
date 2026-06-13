# OOXML snippet library — Thai runs (szCs fallback path)

**Use these only when the house named styles (`ThaiTranslate`, `Heading1`, etc.)
are unavailable in the target document.** When styles are present, apply
`para.style = "ThaiTranslate"` instead — it bakes in AngsanaUPC, blue `#0000FF`,
and correct szCs automatically without raw OOXML.

---

**Font:** **AngsanaUPC** (NOT "Angsana New") in all snippets below.
Replace `>TEXT<` with your content; XML-escape `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`.
All snippets include BOTH `<w:sz>` and `<w:szCs>` and OMIT `<w:cs/>` — required so Thai glyphs render at the correct size.

Insert into a **content-scoped range** only:
- Body paragraph: `thPara.getRange("Content").insertOoxml(pkg, "Replace")`
- Table cell: `cell.body.search(thaiText).getFirst().insertOoxml(pkg, "Replace")`

Do NOT insert into a paragraph-scoped or table-scoped range — those re-nest a table or throw GeneralException.

---

## TH body / list (AngsanaUPC 14pt → sz/szCs 28, blue)
```xml
<?xml version="1.0" standalone="yes"?>
<pkg:package xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage"><pkg:part pkg:name="/_rels/.rels" pkg:contentType="application/vnd.openxmlformats-package.relationships+xml"><pkg:xmlData><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships></pkg:xmlData></pkg:part><pkg:part pkg:name="/word/document.xml" pkg:contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"><pkg:xmlData><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:rPr><w:rFonts w:ascii="AngsanaUPC" w:hAnsi="AngsanaUPC" w:cs="AngsanaUPC"/><w:color w:val="0000FF"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr><w:t xml:space="preserve">TEXT</w:t></w:r></w:p></w:body></w:document></pkg:xmlData></pkg:part></pkg:package>
```

## TH Heading1 sibling (AngsanaUPC 14pt → sz/szCs 28, blue, bold)
```xml
<?xml version="1.0" standalone="yes"?>
<pkg:package xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage"><pkg:part pkg:name="/_rels/.rels" pkg:contentType="application/vnd.openxmlformats-package.relationships+xml"><pkg:xmlData><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships></pkg:xmlData></pkg:part><pkg:part pkg:name="/word/document.xml" pkg:contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"><pkg:xmlData><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:rPr><w:rFonts w:ascii="AngsanaUPC" w:hAnsi="AngsanaUPC" w:cs="AngsanaUPC"/><w:b/><w:color w:val="0000FF"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr><w:t xml:space="preserve">TEXT</w:t></w:r></w:p></w:body></w:document></pkg:xmlData></pkg:part></pkg:package>
```

## TH safety callout (AngsanaUPC 14pt, blue, shaded #FFF2CC)
```xml
<?xml version="1.0" standalone="yes"?>
<pkg:package xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage"><pkg:part pkg:name="/_rels/.rels" pkg:contentType="application/vnd.openxmlformats-package.relationships+xml"><pkg:xmlData><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships></pkg:xmlData></pkg:part><pkg:part pkg:name="/word/document.xml" pkg:contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"><pkg:xmlData><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="FFF2CC"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="AngsanaUPC" w:hAnsi="AngsanaUPC" w:cs="AngsanaUPC"/><w:color w:val="0000FF"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr><w:t xml:space="preserve">TEXT</w:t></w:r></w:p></w:body></w:document></pkg:xmlData></pkg:part></pkg:package>
```

## Verify each run after insert
```js
const xml = thPara.getOoxml(); await ctx.sync();
const ok = /w:szCs/.test(xml.value) && !/<w:cs\/>/.test(xml.value);
```

<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:fb="http://www.gribuser.ru/xml/fictionbook/2.0"
	xmlns:ext="http://exslt.org/common"
	xmlns:regexp="http://exslt.org/regular-expressions"
	xmlns:rupor="fb2mobi_ns" extension-element-prefixes="rupor regexp ext"
	exclude-result-prefixes="fb">

	<xsl:output method="xml" encoding="UTF-8" indent="no"/>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="node()|@*" mode="pass2">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="pass2"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="/">
		<xsl:variable name="pass1res">
			<xsl:apply-templates/>
		</xsl:variable>
		<xsl:apply-templates mode="pass2" select="ext:node-set($pass1res)/*"/>
	</xsl:template>

	<xsl:template match="fb:p/text()">
		<xsl:value-of select="regexp:replace(., '(\u0020|\u00A0|\u1680|\u180E|\u2000|\u2001|\u2002|\u2003|\u2004|\u2005|\u2006|\u2007|\u2008|\u2009|\u200A|\u200B|\u200F|\u3000)[‐‑−–—―](\u0020|\u00A0|\u1680|\u180E|\u2000|\u2001|\u2002|\u2003|\u2004|\u2005|\u2006|\u2007|\u2008|\u2009|\u200A|\u200B|\u200F|\u3000)', 'g', '\1—\2')"/>
	</xsl:template>

	<xsl:template mode="pass2" match="fb:p[starts-with(.,'‐') or starts-with(.,'‑') or starts-with(.,'−') or starts-with(.,'–') or starts-with(.,'—') or starts-with(.,'―') or starts-with(.,'…')]" priority="2">
			<rupor:katz_tr>—&#8198;</rupor:katz_tr>
	</xsl:template>

</xsl:stylesheet>
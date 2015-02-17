<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fb="http://www.gribuser.ru/xml/fictionbook/2.0">
	<xsl:output method="xml" encoding="UTF-8" indent="no"/>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="fb:p">
		<xsl:choose>
			<xsl:when test="starts-with(.,'– ')">
				<xsl:element name="p" namespace="http://www.gribuser.ru/xml/fictionbook/2.0">
					<xsl:text disable-output-escaping="yes">–&amp;emsp;</xsl:text>
					<xsl:value-of select="substring(.,3)"/>
				</xsl:element>
			</xsl:when>
			<xsl:when test="starts-with(.,'–')">
				<xsl:element name="p" namespace="http://www.gribuser.ru/xml/fictionbook/2.0">
					<xsl:text disable-output-escaping="yes">–&amp;emsp;</xsl:text>
					<xsl:value-of select="substring(.,2)"/>
				</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
					<xsl:apply-templates/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

</xsl:stylesheet>
'use client';

import { memo, useEffect, useRef, useState } from 'react';
import styles from './dialoguePage.module.css';
import type { KnowledgeGraphData } from '../lib/dialogue-types';

type Props = { graph: KnowledgeGraphData };

type SimNode = {
  id: string;
  label: string;
  color: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
  index?: number;
};

type SimLink = {
  source: SimNode;
  target: SimNode;
  label: string;
  id: string;
};

const NODE_COLORS = ['#4F8EF7', '#F76B6B', '#59C97F', '#F7B84F', '#A37FE8'];
const LOAD_DURATION = 30_000;
const FADE_DURATION = 450;

function nodeColor(id: string): string {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) & 0xfffffff;
  return NODE_COLORS[h % NODE_COLORS.length];
}

export default memo(function KnowledgeGraphMessage({ graph }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [counts, setCounts] = useState({ nodes: 0, edges: 0 });
  const total = { nodes: graph.nodes.length, edges: graph.edges.length };

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;

    let stopped = false;
    const timers: ReturnType<typeof setTimeout>[] = [];

    void import('d3').then((d3) => {
      if (stopped || !svgRef.current) return;

      const width = 760;
      const height = 420;
      const svg = d3.select(el);
      svg.selectAll('*').remove();

      const defs = svg.append('defs');

      defs.append('marker')
        .attr('id', 'kg-arrow')
        .attr('viewBox', '0 -4 8 8')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4')
        .attr('fill', 'rgba(0,0,0,0.22)');

      const pid = `kg-dots-${Math.random().toString(36).slice(2, 7)}`;
      const pat = defs.append('pattern')
        .attr('id', pid).attr('width', 26).attr('height', 26)
        .attr('patternUnits', 'userSpaceOnUse');
      pat.append('circle').attr('cx', 2).attr('cy', 2).attr('r', 1.4)
        .attr('fill', 'rgba(137,151,181,0.22)');
      svg.append('rect').attr('width', width).attr('height', height)
        .attr('fill', `url(#${pid})`);

      const g = svg.append('g');
      svg.call(
        d3.zoom<SVGSVGElement, unknown>()
          .scaleExtent([0.15, 4])
          .on('zoom', (ev) => g.attr('transform', ev.transform)),
      );

      const nodes: SimNode[] = graph.nodes.map((n) => ({
        id: n.id, label: n.label, color: nodeColor(n.id), x: n.x, y: n.y,
      }));
      const nodeById = new Map(nodes.map((n) => [n.id, n]));
      const links: SimLink[] = graph.edges
        .filter((e) => nodeById.has(e.from) && nodeById.has(e.to))
        .map((e) => ({
          source: nodeById.get(e.from)!,
          target: nodeById.get(e.to)!,
          label: e.label,
          id: e.id,
        }));

      const nCount = nodes.length;
      const lCount = links.length;

      const simulation = d3.forceSimulation<SimNode>(nodes)
        .force('link', d3.forceLink<SimNode, SimLink>(links)
          .id((d) => d.id).distance(88).strength(0.55))
        .force('charge', d3.forceManyBody<SimNode>().strength(-220))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide<SimNode>(28));

      // edges — initially invisible
      const linkSel = g.append('g')
        .selectAll<SVGLineElement, SimLink>('line')
        .data(links).join('line')
        .attr('stroke', 'rgba(0,0,0,0.18)')
        .attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#kg-arrow)')
        .style('opacity', 0);

      // edge labels (≤28 edges)
      const showEdgeLabels = links.length <= 28;
      const edgeLabelSel = showEdgeLabels
        ? g.append('g')
            .selectAll<SVGGElement, SimLink>('g')
            .data(links).join('g')
            .style('opacity', 0)
        : null;

      if (edgeLabelSel) {
        edgeLabelSel.append('rect')
          .attr('rx', 3).attr('fill', 'rgba(239,237,228,0.9)')
          .attr('stroke', 'rgba(0,0,0,0.08)').attr('stroke-width', 0.8);
        const textSel = edgeLabelSel.append('text')
          .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
          .attr('fill', 'rgba(0,0,0,0.4)').attr('font-size', 9)
          .attr('font-family', 'monospace')
          .text((d) => d.label);
        textSel.each(function () {
          const parent = d3.select(this.parentNode as Element);
          try {
            const bbox = (this as SVGTextElement).getBBox();
            parent.select('rect')
              .attr('x', bbox.x - 3).attr('y', bbox.y - 2)
              .attr('width', bbox.width + 6).attr('height', bbox.height + 4);
          } catch { /* getBBox unavailable in test env */ }
        });
      }

      // nodes — initially invisible
      const drag = d3.drag<SVGGElement, SimNode>()
        .on('start', (ev, d) => {
          if (!ev.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
        .on('end', (ev, d) => {
          if (!ev.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        });

      const nodeSel = g.append('g')
        .selectAll<SVGGElement, SimNode>('g')
        .data(nodes).join('g')
        .style('cursor', 'grab')
        .style('opacity', 0)
        .call(drag);

      nodeSel.append('circle')
        .attr('r', 10).attr('fill', (d) => d.color)
        .attr('stroke', '#000').attr('stroke-width', 1.5);

      if (nodes.length <= 42) {
        nodeSel.append('text')
          .attr('x', 14).attr('y', 4).attr('font-size', 11)
          .attr('font-family', 'var(--font-geist-sans),Arial,sans-serif')
          .attr('fill', '#111')
          .text((d) => d.label);
      }

      simulation.on('tick', () => {
        linkSel
          .attr('x1', (d) => (d.source as SimNode).x ?? 0)
          .attr('y1', (d) => (d.source as SimNode).y ?? 0)
          .attr('x2', (d) => (d.target as SimNode).x ?? 0)
          .attr('y2', (d) => (d.target as SimNode).y ?? 0);

        edgeLabelSel?.attr('transform', (d) => {
          const mx = ((d.source as SimNode).x! + (d.target as SimNode).x!) / 2;
          const my = ((d.source as SimNode).y! + (d.target as SimNode).y!) / 2;
          return `translate(${mx},${my})`;
        });

        nodeSel.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });

      // staggered reveal — nodes
      nodes.forEach((_, i) => {
        const delay = nCount <= 1 ? 0 : (i / (nCount - 1)) * LOAD_DURATION;
        const t = setTimeout(() => {
          if (stopped) return;
          d3.select(nodeSel.nodes()[i])
            .transition().duration(FADE_DURATION).style('opacity', 1);
          setCounts((c) => ({ ...c, nodes: i + 1 }));
        }, delay);
        timers.push(t);
      });

      // staggered reveal — edges (interleaved with nodes)
      links.forEach((_, i) => {
        const delay = lCount <= 1 ? 0 : (i / (lCount - 1)) * LOAD_DURATION;
        const t = setTimeout(() => {
          if (stopped) return;
          d3.select(linkSel.nodes()[i])
            .transition().duration(FADE_DURATION).style('opacity', 1);
          if (edgeLabelSel) {
            d3.select(edgeLabelSel.nodes()[i])
              .transition().duration(FADE_DURATION).style('opacity', 1);
          }
          setCounts((c) => ({ ...c, edges: i + 1 }));
        }, delay);
        timers.push(t);
      });
    });

    return () => {
      stopped = true;
      timers.forEach(clearTimeout);
    };
  }, [graph]);

  return (
    <div className={styles.graphCanvas}>
      <div className={styles.graphStatus}>
        <span>nodes {counts.nodes}/{total.nodes}</span>
        <span>edges {counts.edges}/{total.edges}</span>
        <span className={styles.graphHint}>可拖拽 · 滚轮缩放</span>
      </div>
      <svg
        ref={svgRef}
        viewBox="0 0 760 420"
        className={styles.graphSvg}
        role="img"
        aria-label="知识图谱"
      />
    </div>
  );
});

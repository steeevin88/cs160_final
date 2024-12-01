"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LineChart, Line, CartesianGrid, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

interface Metrics {
  timestamp: number;
  responseTime: number;
  successRate: number;
  cpuUsage: number;
  activeAttackers: number;
}

interface MetricsChartProps {
  data: Metrics[];
}

const chartConfig = {
  responseTime: {
    label: "Response Time",
    color: "hsl(var(--chart-1))",
  },
  successRate: {
    label: "Success Rate",
    color: "hsl(var(--chart-2))",
  },
  cpuUsage: {
    label: "CPU Usage",
    color: "hsl(var(--chart-3))",
  },
  activeAttackers: {
    label: "Active Attackers",
    color: "hsl(var(--chart-4))",
  },
};

const MetricsChart = ({ data }: MetricsChartProps) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="h-[300px] w-full flex items-center justify-center">
        <div className="text-gray-500">Loading chart...</div>
      </div>
    );
  }

  const formattedData = data.map((item) => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString(),
    responseTime: item.responseTime,
    successRate: item.successRate,
    cpuUsage: item.cpuUsage,
    activeAttackers: item.activeAttackers,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Attack Metrics</CardTitle>
        <CardDescription>Real-time performance metrics</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px]">
          <LineChart data={formattedData} className="w-full">
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickLine={false}
              axisLine={false}
              tickMargin={10}
              tickFormatter={(value) => value.slice(0, 5)}
            />
            <YAxis tickLine={false} axisLine={false} tickMargin={10} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line
              type="monotone"
              dataKey="responseTime"
              stroke="var(--color-responseTime)"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="successRate"
              stroke="var(--color-successRate)"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="cpuUsage"
              stroke="var(--color-cpuUsage)"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="activeAttackers"
              stroke="var(--color-activeAttackers)"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
};

export default MetricsChart;

"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import MetricsChart from "@/components/MetricsChart";

interface Metrics {
  timestamp: number;
  responseTime: number;
  successRate: number;
  cpuUsage: number;
  activeAttackers: number;
}

interface Log {
  timestamp: string;
  type: "error" | "warning" | "info";
  message: string;
}

export default function Home() {
  const [numThreads, setNumThreads] = useState(10);
  const [rateLimit, setRateLimit] = useState(5);
  const [attackMode, setAttackMode] = useState("single");
  const [targetEndpoint, setTargetEndpoint] = useState("/limited");
  const [metrics, setMetrics] = useState<Metrics[]>([]);
  const [useBlacklist, setUseBlacklist] = useState(false);
  const [logs, setLogs] = useState<Log[]>([]);
  const [isAttacking, setIsAttacking] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isAttacking) {
      const fetchMetrics = async () => {
        try {
          const response = await fetch("http://localhost:8000/metrics");
          if (!response.ok) {
            if (response.status === 429) {
              const data = await response.json();
              setMetrics((prev) =>
                [
                  ...prev,
                  {
                    timestamp: Date.now(),
                    ...data,
                  },
                ].slice(-20)
              );
              return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          setMetrics((prev) =>
            [
              ...prev,
              {
                timestamp: Date.now(),
                ...data,
              },
            ].slice(-20)
          );
        } catch (error) {
          console.error("Error fetching metrics:", error);
        }
      };

      const fetchLogs = async () => {
        try {
          const response = await fetch("http://localhost:8000/logs");
          if (!response.ok) {
            if (response.status === 429) {
              const data = await response.json();
              if (Array.isArray(data)) {
                setLogs(data.slice(-100));
              }
              return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          if (Array.isArray(data)) {
            setLogs(data.slice(-100));
          }
        } catch (error) {
          console.error("Error fetching logs:", error);
        }
      };

      fetchMetrics();
      fetchLogs();

      const metricsInterval = setInterval(fetchMetrics, 1000);
      const logsInterval = setInterval(fetchLogs, 2000);

      return () => {
        clearInterval(metricsInterval);
        clearInterval(logsInterval);
      };
    }
  }, [isAttacking]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsAttacking(true);

    try {
      const response = await fetch("http://localhost:8000/configure", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          NUM_THREADS: numThreads,
          RATE_LIMIT: rateLimit,
          ATTACK_MODE: attackMode,
          TARGET_ENDPOINT: targetEndpoint,
          IS_BLACKLISTING: useBlacklist,
        }),
      });

      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error("Error configuring attack:", error);
      setIsAttacking(false);
    }
  };

  const stopAttack = async () => {
    try {
      await fetch("http://localhost:8000/stop", { method: "POST" });
      setIsAttacking(false);
      setMetrics([]);
      setLogs([]);
    } catch (error) {
      console.error("Error stopping attack:", error);
    }
  };

  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen p-8 bg-gray-100">
      <div className="max-w-7xl mx-auto space-y-8">
        <h1 className="text-4xl font-bold">DoS/DDoS Attack Simulator</h1>

        <div className="grid grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Attack Configuration</CardTitle>
              <CardDescription>
                Configure your attack parameters
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Attack Mode</Label>
                  <Select value={attackMode} onValueChange={setAttackMode}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select attack mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="single">Single DoS</SelectItem>
                      <SelectItem value="distributed">
                        Distributed DoS
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Target Endpoint</Label>
                  <Select
                    value={targetEndpoint}
                    onValueChange={setTargetEndpoint}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select target endpoint" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="/limited">
                        Rate Limited Endpoint
                      </SelectItem>
                      <SelectItem value="/open">Open Endpoint</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="useBlacklist"
                    checked={useBlacklist}
                    onCheckedChange={(checked) => setUseBlacklist(checked as boolean)}
                  />
                  <Label htmlFor="useBlacklist">Use Blacklist</Label>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="numThreads">
                    Number of Attackers: {numThreads}
                  </Label>
                  <Slider
                    id="numThreads"
                    min={1}
                    max={100}
                    step={1}
                    value={[numThreads]}
                    onValueChange={(value) => setNumThreads(value[0])}
                  />
                </div>

                {targetEndpoint !== "/open" && (
                  <div className="space-y-2">
                    <Label htmlFor="rateLimit">
                      Rate Limit (requests per minute)
                    </Label>
                    <Input
                      id="rateLimit"
                      type="number"
                      value={rateLimit}
                      onChange={(e) => setRateLimit(Number(e.target.value))}
                      placeholder="e.g., 5"
                      min={1}
                    />
                  </div>
                )}
              </CardContent>
              <CardFooter className="space-x-2">
                <Button type="submit" disabled={isAttacking}>
                  Start Attack
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  onClick={stopAttack}
                  disabled={!isAttacking}
                >
                  Stop Attack
                </Button>
              </CardFooter>
            </form>
          </Card>

          <div>
            <MetricsChart data={metrics} />
          </div>

          <Card className="col-span-2">
            <CardHeader>
              <CardTitle>Attack Logs</CardTitle>
              <CardDescription>
                Real-time attack and defense logs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px] w-full rounded-md border p-4">
                {Array.isArray(logs) && logs.length > 0 ? (
                  <div className="space-y-2">
                    {logs.map((log, index) => (
                      <div key={index} className="py-1 text-sm">
                        <span className="text-gray-500 font-mono">
                          {log.timestamp}
                        </span>
                        <span
                          className={`ml-2 font-semibold ${
                            log.type === "error"
                              ? "text-red-500"
                              : log.type === "warning"
                              ? "text-yellow-500"
                              : "text-green-500"
                          }`}
                        >
                          [{log.type}]
                        </span>
                        <span className="ml-2 font-mono">{log.message}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500">
                    No logs available
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

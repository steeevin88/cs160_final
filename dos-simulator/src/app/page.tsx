'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"

export default function Home() {
  const [numThreads, setNumThreads] = useState(10)
  const [rateLimit, setRateLimit] = useState(5)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    const response = await fetch('http://localhost:8000/configure', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        NUM_THREADS: numThreads,
        RATE_LIMIT: rateLimit,
      }),
    })

    const data = await response.json()
    console.log(data)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>DoS Simulation Configuration</CardTitle>
          <CardDescription>Configure the parameters for your DoS simulation</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="numThreads">Number of Threads: {numThreads}</Label>
              <Slider
                id="numThreads"
                min={1}
                max={100}
                step={1}
                value={[numThreads]}
                onValueChange={(value) => setNumThreads(value[0])}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="rateLimit">Rate Limit (requests per minute)</Label>
              <Input
                id="rateLimit"
                type="number"
                value={rateLimit}
                onChange={(e) => setRateLimit(Number(e.target.value))}
                placeholder="e.g., 5"
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full">Submit Configuration</Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}

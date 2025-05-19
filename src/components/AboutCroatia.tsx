
import React from 'react';
import { MapPinIcon } from 'lucide-react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

const AboutCroatia = () => {
  const regions = [
    {
      id: 'dalmatia',
      name: 'Dalmatia',
      description: 'Known for its stunning coastline with crystal-clear waters, historic cities like Split and Dubrovnik, and beautiful islands. Dalmatia offers a perfect blend of history, culture, and natural beauty.',
      attractions: ['Diocletian\'s Palace in Split', 'Dubrovnik Old Town', 'Krka National Park', 'Hvar Island', 'Zadar Sea Organ'],
      imageUrl: '/about-image.jpg'
    },
    {
      id: 'istria',
      name: 'Istria',
      description: 'Croatia\'s heart-shaped peninsula known for its rolling hills, medieval hilltop towns, truffles, and excellent wines. Istria showcases a unique blend of Croatian and Italian influences.',
      attractions: ['Pula Arena', 'Rovinj Old Town', 'Motovun', 'Brijuni National Park', 'Grožnjan'],
      imageUrl: '/about-image.jpg'
    },
    {
      id: 'zagreb',
      name: 'Zagreb Region',
      description: 'The capital region offers a mix of Austro-Hungarian architecture, vibrant cultural scene, and charming streets. Zagreb itself is known for its museums, cafes, and historic Upper Town.',
      attractions: ['St. Mark\'s Church', 'Dolac Market', 'Museum of Broken Relationships', 'Mirogoj Cemetery', 'Lotrščak Tower'],
      imageUrl: '/about-image.jpg'
    },
    {
      id: 'slavonia',
      name: 'Slavonia',
      description: 'The eastern region of Croatia known for its plains, oak forests, vineyards, and rich folk traditions. Slavonia offers authentic cultural experiences away from tourist crowds.',
      attractions: ['Kopački Rit Nature Park', 'Osijek Fortress', 'Đakovo Cathedral', 'Ilok vineyards', 'Papuk Nature Park'],
      imageUrl: '/about-image.jpg'
    },
    {
      id: 'kvarner',
      name: 'Kvarner',
      description: 'A coastal region with beautiful islands, historic resorts, and the port city of Rijeka. The area combines mountains meeting the sea with Habsburg-era architecture.',
      attractions: ['Opatija Riviera', 'Island of Krk', 'Učka Nature Park', 'Rijeka Carnival', 'Island of Rab'],
      imageUrl: '/about-image.jpg'
    }
  ];

  return (
    <section className="mb-12 relative overflow-hidden rounded-lg shadow-lg bg-gradient-to-r from-navy-blue to-medium-blue text-white">
      <div className="absolute inset-0 z-0 opacity-20 bg-[url('/about-image.jpg')] bg-cover bg-center"></div>
      
      <div className="relative z-10 p-8">
        <div className="flex flex-col md:flex-row gap-8">
          <div className="md:w-1/3">
            <h2 className="text-3xl font-bold mb-4 font-sreda flex items-center gap-2">
              <MapPinIcon size={24} />
              About Croatia
            </h2>
            <p className="mb-4 font-josefin">
              Croatia offers a remarkable blend of natural beauty, rich history, and vibrant culture. From the pristine Adriatic coastline to historic cities and lush national parks, this Mediterranean gem has something for every traveler.
            </p>
            <p className="font-josefin">
              Explore Croatia's diverse regions, each with its own unique character and attractions. From the sunny islands of Dalmatia to the rolling hills of Istria and the vibrant capital of Zagreb, discover what makes Croatia one of Europe's most captivating destinations.
            </p>
          </div>
          
          <div className="md:w-2/3">
            <Tabs defaultValue={regions[0].id} className="w-full">
              <div className="mb-4 overflow-x-auto pb-1">
                <TabsList className="bg-transparent h-auto w-full justify-start space-x-2 rounded-none border-b border-white/20">
                  {regions.map((region) => (
                    <TabsTrigger 
                      key={region.id} 
                      value={region.id}
                      className="text-white/70 data-[state=active]:text-white data-[state=active]:border-b-2 data-[state=active]:border-white data-[state=active]:bg-transparent px-4 py-2 rounded-none"
                    >
                      {region.name}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </div>
              
              {regions.map((region) => (
                <TabsContent key={region.id} value={region.id} className="mt-0">
                  <div className="p-4 bg-white/10 backdrop-blur-sm rounded-lg">
                    <h3 className="text-xl font-bold mb-3 font-sreda">{region.name}</h3>
                    <p className="mb-4 font-josefin">{region.description}</p>
                    
                    <h4 className="text-lg font-bold mb-2">Top Attractions:</h4>
                    <ul className="list-disc pl-6 space-y-1">
                      {region.attractions.map((attraction, index) => (
                        <li key={index} className="font-josefin">{attraction}</li>
                      ))}
                    </ul>
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutCroatia;

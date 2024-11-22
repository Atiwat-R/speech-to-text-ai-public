import Head from 'next/head';
import TextDisplay from './component/TextDisplay';
import '../styles/globals.css';
import './globals.css';
import language from '../../../language.json'

export default function Home() {

    return (
        <div>
            <Head>
                <title>Live Transcription Display</title>
                <meta name="description" content="Displays live transcription from a text file" />
                <link rel="icon" href="/favicon.ico" />
            </Head>
            <main>

            </main>

            <div className="h-screen flex flex-col">
                {/* Top equal partitions */}
                <div className="flex-1 flex items-left pt-10 justify-start bg-black top-10">
                    <div className="px-20 text-7xl text-left leading-25 text-white mb-10 font-bold font-thai uppercase">
                        <TextDisplay path={'/api/transcription'}/>
                    </div>
                </div>
                <div className="flex-1 flex items-left pt-10 justify-start bg-black bottom-10">
                    <div className="px-20 text-7xl text-left leading-[7rem] text-white mb-10 font-bold font-thai uppercase">
                        <TextDisplay path={'/api/translated-transcription'}/>
                    </div>
                </div>
                {/* Bottom smaller partition */}
            </div>
        </div>
    );
}

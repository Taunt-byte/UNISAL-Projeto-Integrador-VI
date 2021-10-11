using System;
using System.Runtime;
using System.Runtime.InteropServices;

using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;

using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using Microsoft.Win32;

namespace NetworkTracer
{
    public partial class Tracer : Form
    {        
        private Timer _timer;
        private DateTime _startTime = DateTime.MinValue;
        private bool _isNetworkOnline;
        IPGlobalProperties properties = IPGlobalProperties.GetIPGlobalProperties();
        IPGlobalStatistics ipstat = null;
        Decimal start_r_packets;
        Decimal end_r_packets;
        NetworkInterface[] fNetworkInterfaces = NetworkInterface.GetAllNetworkInterfaces();
        long start_received_bytes;
        long start_sent_bytes;
        long end_received_bytes;
        long end_sent_bytes;

        public Tracer()
        {
            // check if connection exist or not

            InitializeComponent();

            btnMonitor.Enabled = true;
            btnCancel.Enabled = false;
            _timer = new Timer();           
            _timer.Tick += new EventHandler(timerTicker);
        }


        protected void startMonitor(object sender, EventArgs e)
        {
            _startTime = DateTime.Now;                        
            _timer.Start();                        
            btnMonitor.Enabled = false;
            btnCancel.Enabled = true;
            ipstat = properties.GetIPv4GlobalStatistics();                     

            getConnectionInfo();
        }

        [DllImport("wininet.dll")]        
        private extern static bool InternetGetConnectedState(out int Description, int ReservedValue);
        public static bool IsConnectedToInternet()
        {
            int Desc;
            return InternetGetConnectedState(out Desc, 0);
        }

        protected void getConnectionInfo()
        {
            try
            {
                string myHost = System.Net.Dns.GetHostName();
                IPHostEntry ipEntry = System.Net.Dns.GetHostEntry(myHost);
                IPAddress[] addr = ipEntry.AddressList;
                NetworkChange.NetworkAvailabilityChanged += new NetworkAvailabilityChangedEventHandler(NetworkChange_NetworkAvailabilityChanged);
                _isNetworkOnline = NetworkInterface.GetIsNetworkAvailable();

                if (addr.Length > 0)
                {
                    start_r_packets = Convert.ToDecimal(ipstat.ReceivedPackets);
                    //start_r_packets = Math.Round(start_r_packets / 1048576 * 100000) / 100000;

                    txtboxInfo.Text = "";
                    txtboxInfo.Text += "IP Address: " + addr[addr.Length - 1].ToString() + Environment.NewLine;
                    
                    NetworkInterface adapter = fNetworkInterfaces[0];

                    start_received_bytes = fNetworkInterfaces[0].GetIPv4Statistics().BytesReceived;
                    start_sent_bytes = fNetworkInterfaces[0].GetIPv4Statistics().BytesSent;                   

                    txtboxInfo.Text += Environment.NewLine + "Name: " + adapter.Name + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "Description: " + adapter.Description + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "Network Type: " + adapter.NetworkInterfaceType + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "Speed: " + adapter.Speed / 1000000 + " (Mbps)" + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "Operational Status: " + adapter.OperationalStatus + Environment.NewLine;

                    txtboxInfo.Text += Environment.NewLine + "Reeived: " + start_received_bytes.ToString() + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "Sent: " + start_sent_bytes.ToString() + Environment.NewLine;

                    start_received_bytes = (start_received_bytes / 1048576 * 100000) / 100000;
                    start_sent_bytes = (start_sent_bytes / 1048576 * 100000) / 100000;

                    txtboxInfo.Text += Environment.NewLine + "Reeived (in MB): " + start_received_bytes.ToString() + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "Sent (in MB): " + start_sent_bytes.ToString() + Environment.NewLine;

                    txtboxInfo.Text += Environment.NewLine + "Is Network Available: " + _isNetworkOnline.ToString() + Environment.NewLine;                    
                    txtboxInfo.Text += Environment.NewLine + "Starting Received Packets: " + start_r_packets.ToString() + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "Is Network up: " + System.Net.NetworkInformation.NetworkInterface.GetIsNetworkAvailable().ToString() + Environment.NewLine;
                    txtboxInfo.Text += Environment.NewLine + "New method output: " + IsConnectedToInternet().ToString();
                }                                
                
            }
            catch (Exception ex)
            {
                txtboxInfo.Text = "Error!" + Environment.NewLine + ex.Message.ToString();
                _timer.Stop();
                lblTime.Text = "";
                btnCancel.Enabled = false;
                btnMonitor.Enabled = false;
            }
        }

        protected void NetworkChange_NetworkAvailabilityChanged(object sender, NetworkAvailabilityEventArgs e) 
        { 
            _isNetworkOnline = e.IsAvailable; 
        } 

        protected void closeEverything(object sender, EventArgs e)
        {
            _timer.Stop();
            btnCancel.Enabled = false;
            btnMonitor.Enabled = true;
            txtboxInfo.Text = lblTime.Text + Environment.NewLine;

            ipstat = properties.GetIPv4GlobalStatistics();
            end_r_packets = Convert.ToDecimal(ipstat.ReceivedPackets);
        //    end_r_packets = Math.Round(end_r_packets / 1048576 * 100000) / 100000;

            txtboxInfo.Text += Environment.NewLine + "Starting Received Packets: " + start_r_packets.ToString() + Environment.NewLine;
            txtboxInfo.Text += Environment.NewLine + "Ending Received Packets: " + end_r_packets.ToString() + Environment.NewLine;
            end_r_packets = end_r_packets - start_r_packets;
            txtboxInfo.Text += Environment.NewLine + "Total Received Packets: " + end_r_packets.ToString() + Environment.NewLine;

            txtboxInfo.Text += Environment.NewLine + "Received Start (in MB): " + start_received_bytes.ToString() + Environment.NewLine;
            txtboxInfo.Text += Environment.NewLine + "Sent Start (in MB): " + start_sent_bytes.ToString() + Environment.NewLine;

            end_received_bytes = fNetworkInterfaces[0].GetIPv4Statistics().BytesReceived;
            end_sent_bytes = fNetworkInterfaces[0].GetIPv4Statistics().BytesSent;

            end_received_bytes = (end_received_bytes / 1048576 * 100000) / 100000;
            end_sent_bytes = (end_sent_bytes / 1048576 * 100000) / 100000;

            txtboxInfo.Text += Environment.NewLine + "Received End (in MB): " + end_received_bytes.ToString() + Environment.NewLine;
            txtboxInfo.Text += Environment.NewLine + "Sent End (in MB): " + end_sent_bytes.ToString() + Environment.NewLine;

            txtboxInfo.Text += Environment.NewLine + "Received Total (in MB): " + (end_received_bytes - start_received_bytes).ToString() + Environment.NewLine;
            txtboxInfo.Text += Environment.NewLine + "Sent Total (in MB): " + (end_sent_bytes - start_sent_bytes).ToString() + Environment.NewLine;

            writetoFile();
        }

        protected void writetoFile()
        {
            string path_file = @"C:\\Documents and Settings\\user2\\Desktop\\Test Tracer.txt";
            string empty_line = "===============================================================";
            if (System.IO.File.Exists(path_file))
            {
                System.IO.File.AppendAllText(path_file, empty_line + Environment.NewLine + "Connection opened: " + _startTime + Environment.NewLine + "Connection Closed: " + DateTime.Now.ToString() + Environment.NewLine + Environment.NewLine + txtboxInfo.Text + Environment.NewLine);
            }
        }

        protected void timerTicker(object sender, EventArgs e)
        {
            var timeSinceStartTime = DateTime.Now - _startTime;
            timeSinceStartTime = new TimeSpan(timeSinceStartTime.Hours,
                                              timeSinceStartTime.Minutes,
                                              timeSinceStartTime.Seconds);                        
            lblTime.Text = "Time: " + timeSinceStartTime.ToString();
        }
    }
}